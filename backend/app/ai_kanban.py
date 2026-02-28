import copy
import time
from typing import Annotated, Literal

from pydantic import BaseModel, Field, model_validator

from app.kanban_schema import BoardModel


class ConversationMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1)


class AIChatRequest(BaseModel):
    message: str = Field(min_length=1)
    history: list[ConversationMessage] = Field(default_factory=list)


class RenameColumnOperation(BaseModel):
    type: Literal["rename_column"]
    columnId: str
    title: str = Field(min_length=1)


class CreateCardOperation(BaseModel):
    type: Literal["create_card"]
    columnId: str
    title: str = Field(min_length=1)
    details: str = "No details yet."
    cardId: str | None = None


class UpdateCardOperation(BaseModel):
    type: Literal["update_card"]
    cardId: str
    title: str | None = None
    details: str | None = None

    @model_validator(mode="after")
    def validate_changes(self) -> "UpdateCardOperation":
        if self.title is None and self.details is None:
            raise ValueError("update_card requires at least one field to update.")
        return self


class MoveCardOperation(BaseModel):
    type: Literal["move_card"]
    cardId: str
    toColumnId: str
    beforeCardId: str | None = None


class DeleteCardOperation(BaseModel):
    type: Literal["delete_card"]
    cardId: str


KanbanOperation = Annotated[
    RenameColumnOperation
    | CreateCardOperation
    | UpdateCardOperation
    | MoveCardOperation
    | DeleteCardOperation,
    Field(discriminator="type"),
]


class AIKanbanResponse(BaseModel):
    assistant_response: str = Field(min_length=1)
    operations: list[KanbanOperation] = Field(default_factory=list)


def _find_column(columns: list[dict[str, object]], column_id: str) -> dict[str, object]:
    for column in columns:
        if column.get("id") == column_id:
            return column
    raise ValueError(f"Column '{column_id}' was not found.")


def _find_column_containing_card(
    columns: list[dict[str, object]], card_id: str
) -> dict[str, object]:
    for column in columns:
        card_ids = column.get("cardIds")
        if isinstance(card_ids, list) and card_id in card_ids:
            return column
    raise ValueError(f"Card '{card_id}' is not assigned to any column.")


def _generate_card_id() -> str:
    return f"card-ai-{time.time_ns()}"


def apply_operations_to_board(
    board_data: dict[str, object],
    operations: list[KanbanOperation],
) -> dict[str, object]:
    if not operations:
        return BoardModel.model_validate(board_data).model_dump()

    next_board = copy.deepcopy(board_data)
    columns = next_board.get("columns")
    cards = next_board.get("cards")

    if not isinstance(columns, list) or not isinstance(cards, dict):
        raise ValueError("Board data is malformed.")

    for operation in operations:
        if isinstance(operation, RenameColumnOperation):
            column = _find_column(columns, operation.columnId)
            column["title"] = operation.title
            continue

        if isinstance(operation, CreateCardOperation):
            column = _find_column(columns, operation.columnId)
            card_id = operation.cardId.strip() if operation.cardId else _generate_card_id()

            if card_id in cards:
                raise ValueError(f"Card id '{card_id}' already exists.")

            cards[card_id] = {
                "id": card_id,
                "title": operation.title,
                "details": operation.details or "No details yet.",
            }

            card_ids = column.get("cardIds")
            if not isinstance(card_ids, list):
                raise ValueError("Column cardIds is malformed.")
            card_ids.append(card_id)
            continue

        if isinstance(operation, UpdateCardOperation):
            card = cards.get(operation.cardId)
            if not isinstance(card, dict):
                raise ValueError(f"Card '{operation.cardId}' was not found.")
            if operation.title is not None:
                card["title"] = operation.title
            if operation.details is not None:
                card["details"] = operation.details
            continue

        if isinstance(operation, MoveCardOperation):
            source_column = _find_column_containing_card(columns, operation.cardId)
            target_column = _find_column(columns, operation.toColumnId)

            source_card_ids = source_column.get("cardIds")
            target_card_ids = target_column.get("cardIds")
            if not isinstance(source_card_ids, list) or not isinstance(target_card_ids, list):
                raise ValueError("Column cardIds is malformed.")

            source_card_ids.remove(operation.cardId)
            if operation.beforeCardId and operation.beforeCardId in target_card_ids:
                target_index = target_card_ids.index(operation.beforeCardId)
                target_card_ids.insert(target_index, operation.cardId)
            else:
                target_card_ids.append(operation.cardId)
            continue

        if isinstance(operation, DeleteCardOperation):
            if operation.cardId not in cards:
                raise ValueError(f"Card '{operation.cardId}' was not found.")
            del cards[operation.cardId]
            for column in columns:
                card_ids = column.get("cardIds")
                if isinstance(card_ids, list):
                    while operation.cardId in card_ids:
                        card_ids.remove(operation.cardId)
            continue

    return BoardModel.model_validate(next_board).model_dump()
