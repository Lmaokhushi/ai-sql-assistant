import json
from unittest import mock

import pytest

from ai_engine import gemini_client, sql_generator, sql_refiner


def test_placeholder_key_counts_as_missing(monkeypatch):
    monkeypatch.setattr(gemini_client, "_load_env", lambda: None)
    monkeypatch.setenv("GEMINI_API_KEY", "paste-your-gemini-api-key-here")
    assert gemini_client.get_api_key() is None
    with pytest.raises(gemini_client.GeminiError):
        gemini_client.ask_gemini("hi")


def test_friendly_errors():
    assert "API key" in gemini_client._friendly_error(Exception("400 API key not valid"))
    assert "rate limit" in gemini_client._friendly_error(Exception("429 RESOURCE_EXHAUSTED"))


def test_generate_strips_fences(shop_schema):
    with mock.patch.object(sql_generator, "ask_gemini", return_value="```sql\nSELECT name FROM customers\n```"):
        assert sql_generator.generate_sql(shop_schema, "names?") == "SELECT name FROM customers"


def test_prompt_includes_history(shop_schema):
    prompt = sql_generator.build_sql_prompt(shop_schema, "and Paris?", "sqlite",
                                            [{"role": "user", "content": "customers in Rome"}])
    assert "customers in Rome" in prompt


def test_refine_validates(shop_schema):
    reply = json.dumps({"diagnosis": "typo", "explanation": "fixed", "can_generate": True,
                        "corrected_sql": "SELECT name FROM customers"})
    with mock.patch.object(sql_refiner, "ask_gemini", return_value=reply):
        result = sql_refiner.refine_sql(shop_schema, "SELECT nme FROM customers", "fix it")
    assert result["success"] and result["validation"]["valid"]


def test_refine_cannot_generate(shop_schema):
    reply = '{"diagnosis": "x", "explanation": "need more", "can_generate": false, "corrected_sql": ""}'
    with mock.patch.object(sql_refiner, "ask_gemini", return_value=reply):
        result = sql_refiner.refine_sql(shop_schema, "SELECT 1", "do something odd")
    assert not result["success"] and result["corrected_sql"] is None
