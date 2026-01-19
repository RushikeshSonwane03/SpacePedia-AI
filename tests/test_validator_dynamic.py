from app.rag.validator import OutputValidator
from app.core.schemas import RAGResponse
import json

def test_validator():
    val = OutputValidator()
    
    # Case 1: Pure List
    list_output = '["Mission A", "Mission B"]'
    res1 = val.validate(list_output)
    print(f"List Test: {res1.answer}")
    assert isinstance(res1, RAGResponse)
    assert "- Mission A" in res1.answer

    # Case 2: Markdown wrapped List
    md_list = "Here is the list: ```json\n['Mission X']\n```"
    # Note: json.loads expects double quotes for strings in JSON standards. LLM often messes this up (single quotes).
    # Python json.loads STRICTLY requires double quotes.
    # If LLM outputs single quotes in list `['a']`, json.loads will FAIL.
    # This is a common failure mode.
    # Let's see if I should handle single quotes fallback?
    
    # Python's ast.literal_eval handles single quotes, but using it on untrusted input is risky?
    # Actually for a RAG app, it's fairly safe if sandboxed? No, `eval` is bad.
    # But `demjson` or `replace`?
    # Let's stick to standard JSON first. If LLM follows "Valid JSON" instruction, it uses double quotes.
    
    # Case 3: Partial Object
    partial = '{"answer": "foo"}' # Missing confidence
    res3 = val.validate(partial)
    print(f"Partial Test: {res3.reasoning}") # Should be "Auto-converted"? No, wait.
    # My code: `RAGResponse(**data)`.
    # Dictionary unpacking. If `confidence` is missing, Pydantic will RAISE VALIDATION ERROR.
    # I need to FIX my validator to handle missing fields in Dict too!
    
    # Case 4: Totally Broken
    broken = "Just some text"
    res4 = val.validate(broken)
    print(f"Broken Test: {res4.confidence}")
    assert res4.confidence == "Low"

if __name__ == "__main__":
    try:
        test_validator()
        print("All tests passed!")
    except Exception as e:
        print(f"Test Failed: {e}")
