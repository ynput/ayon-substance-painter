from ayon_server.settings import BaseSettingsModel, SettingsField


class BasicEnabledModel(BaseSettingsModel):
    enabled: bool = SettingsField(title="Enabled")
    optional: bool = SettingsField(title="Optional")
    active: bool = SettingsField(title="Active")


class PublishersModel(BaseSettingsModel):
    ExtractMakeTX: BasicEnabledModel = SettingsField(
        default_factory=BasicEnabledModel,
        title="Extract Make TX",
    )


DEFAULT_PUBLISH_SETTINGS = {
    "ExtractMakeTX": {
        "enabled": True,
        "optional": True,
        "active": True,
    },
}
