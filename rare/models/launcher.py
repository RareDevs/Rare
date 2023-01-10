from dataclasses import dataclass


class Actions:
    finished = 0
    error = 1
    message = 2
    state_update = 3


@dataclass
class BaseModel:
    action: int
    app_name: str

    @classmethod
    def from_json(cls, data: dict):
        return cls(
            action=data["action"],
            app_name=data["app_name"]
        )


@dataclass
class FinishedModel(BaseModel):
    exit_code: int
    playtime: int  # seconds

    @classmethod
    def from_json(cls, data):
        return cls(
            **BaseModel.from_json(data).__dict__,
            exit_code=data["exit_code"],
            playtime=data["playtime"],
        )


@dataclass
class StateChangedModel(BaseModel):
    class States:
        started = 0

        # for future
        syncing_cloud = 1
        cloud_sync_finished = 2

    new_state: int

    @classmethod
    def from_json(cls, data):
        return cls(
            action=data["action"],
            app_name=data["app_name"],
            new_state=data["new_state"]
        )


@dataclass
class ErrorModel(BaseModel):
    error_string: str

    @classmethod
    def from_json(cls, data):
        return cls(
            **BaseModel.from_json(data).__dict__,
            error_string=data["error_string"]
        )
