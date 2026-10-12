import json

from utils import save_conversation


def test_save_conversation_creates_directory(tmp_path):
    filename = tmp_path / "data" / "conversation.json"

    conversation = [
        {"role": "system", "content": "Test system prompt"},
        {"role": "user", "content": "Hello"},
    ]

    save_conversation(conversation, filename)

    assert filename.is_file()
    assert json.loads(filename.read_text()) == conversation
