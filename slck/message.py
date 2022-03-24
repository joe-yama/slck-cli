from dataclasses import dataclass
from typing import Dict, List

from slack_sdk import WebClient
from slack_sdk.web import SlackResponse
from slck.channel import ChannelManager
from slck.user import User


@dataclass
class Message:
    message_type: str
    user: User
    ts: str
    text: str
    num_reply: int
    num_replyuser: int
    num_reaction: int


def parse_message(message: Dict) -> Message:
    message_type: str = message["type"]
    user: User = User(id=message["user"])
    ts: str = message["ts"]
    text: str = message["text"]
    num_reply: int = message.get("reply_count", 0)
    num_replyuser: int = len(message.get("reply_users", []))
    reactions: List = message.get("reactions", [])
    num_reaction = sum([reaction.get("count", 0) for reaction in reactions])
    return Message(
        message_type=message_type,
        user=user,
        ts=ts,
        text=text,
        num_reply=num_reply,
        num_replyuser=num_replyuser,
        num_reaction=num_reaction,
    )


class MessageManager:
    def __init__(self, client: WebClient) -> None:
        self.client = client

    def list(
        self,
        channel_name: str = "",
        channel_id: str = "",
    ) -> List[Message]:
        if channel_id == "" and channel_name == "":
            raise ValueError(
                "One of arguments (channel_id or channel_name) is required."
            )
        if channel_id and channel_name:
            raise ValueError(
                """
                Recieved both of channel_id and channel_name.
                Desired: Either one of arguments (channel_id or channel_name).
            """
            )
        if channel_name:
            channel_manager: ChannelManager = ChannelManager(self.client)
            channel_id = channel_manager.find(name=channel_name)["id"]

        messages: List[Message] = []
        next_cursor: str = ""  # for pagenation
        while True:
            response: SlackResponse = self.client.conversations_history(
                channel=channel_id, next_cursor=next_cursor
            )
            for message in response["messages"]:
                if message["type"] == "message":
                    m = parse_message(message)
                    messages.append(m)
            if response["has_more"] is True:
                next_cursor = response["response_metadata"]["next_cursor"]
            else:
                break
        return messages
