from ayon_server.settings import BaseSettingsModel, SettingsField


class ChannelMappingItemModel(BaseSettingsModel):
    _layout = "compact"
    name: str = SettingsField(title="Channel Type")
    value: str = SettingsField(title="Channel Map")


class CreateTextureModel(BaseSettingsModel):
    channel_mapping: list[ChannelMappingItemModel] = SettingsField(
        default_factory=list, title="Channel Mapping")


class CreatorsModel(BaseSettingsModel):
    CreateTextures: CreateTextureModel = SettingsField(
        default_factory=CreateTextureModel,
        title="Create Textures"
    )


DEFAULT_CREATOR_SETTINGS = {
    "CreateTextures": {
        "channel_mapping": [
            {"name": "Anisotropy Angle", "value": "Anisotropyangle"},
            {"name": "Anisotropy Level", "value": "Anisotropylevel"},
            {"name": "Base Color", "value": "BaseColor"},
            {"name": "Metallic", "value": "Metallic"},
            {"name": "Roughness", "value": "Roughness"},
            {"name": "Normal", "value": "Normal"},
            {"name": "Height", "value": "Height"},
            {"name": "Specular Edge Color", "value": "SpecularEdgeColor"},
            {"name": "Opacity", "value": "Opacity"},
            {"name": "Displacement", "value": "Displacement"},
            {"name": "Glossiness", "value": "Glossiness"},
            {"name": "Ambient Occlusion", "value": "AO"},
            {"name": "Transmissive", "value": "Transmissive"},
            {"name": "Reflection", "value": "Reflection"},
            {"name": "Diffuse", "value": "Diffuse"},
            {"name": "Index of Refraction", "value": "Ior"},
            {"name": "Specular Level", "value": "Specularlevel"},
            {"name": "Blending Mask", "value": "BlendingMask"},
            {"name": "Translucency", "value": "Translucency"},
            {"name": "Scattering", "value": "Scattering"},
            {"name": "Scatter Color", "value": "ScatterColor"},
            {"name": "Sheen Opacity", "value": "SheenOpacity"},
            {"name": "Sheen Color", "value": "SheenColor"},
            {"name": "Coat Opacity", "value": "CoatOpacity"},
            {"name": "Coat Color", "value": "CoatColor"},
            {"name": "Coat Roughness", "value": "CoatRoughness"},
            {"name": "Coat Specular Level", "value": "CoatSpecularLevel"},
            {"name": "Coat Normal", "value": "CoatNormal"}
        ],
    }
}
