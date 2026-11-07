from __future__ import annotations

import argparse
from pathlib import Path

from agent.core import Agent, AgentConfig, load_openai_api_key_from_dotenv
from bridge.core import Allowlist, MessagesBridge
from .core import ConversationProcessor, CostPolicy, ProcessingStateStore


def main() -> None:
    parser = argparse.ArgumentParser(description="Poll authorized iMessages and queue approval-gated AI replies")
    parser.add_argument("--allowlist", type=Path, required=True)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--database", type=Path)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--list-pending", action="store_true")
    parser.add_argument("--show-private", action="store_true", help="show sender and reply text in pending output")
    parser.add_argument("--activate", action="store_true", help="record the current Messages watermark and skip history")
    parser.add_argument("--approve")
    parser.add_argument("--reject")
    parser.add_argument("--cancel")
    args = parser.parse_args()
    bridge = MessagesBridge(Allowlist.load(args.allowlist), args.database)
    processor = ConversationProcessor(
        bridge,
        Agent(AgentConfig()),
        ProcessingStateStore(args.state),
        offline=args.offline,
    )
    actions = [args.list_pending, args.activate, bool(args.approve), bool(args.reject), bool(args.cancel)]
    if sum(actions) > 1:
        parser.error("choose only one approval-queue action")
    if args.list_pending:
        for record in processor.state.pending():
            if args.show_private:
                print(f"source={record.source_id} sender={record.sender} reply={record.reply_text}")
            else:
                print(f"source={record.source_id} status={record.status}")
    elif args.activate:
        load_openai_api_key_from_dotenv()
        watermark = processor.activate()
        print(f"activated watermark_recorded={watermark is not None}; historical messages will be skipped")
    elif args.approve:
        record = processor.approve(args.approve)
        print(f"approved source={record.source_id} status={record.status}; verify delivery separately")
    elif args.reject:
        record = processor.reject(args.reject)
        print(f"rejected source={record.source_id} status={record.status}")
    elif args.cancel:
        record = processor.cancel(args.cancel)
        print(f"cancelled source={record.source_id} status={record.status}")
    else:
        load_openai_api_key_from_dotenv()
        for record in processor.poll(args.limit):
            print(f"source={record.source_id} status={record.status}")


if __name__ == "__main__":
    main()
