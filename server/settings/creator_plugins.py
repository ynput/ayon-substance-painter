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
            {"name": "Anisotropy Angle",
             "value": "_Anisotropyangle"},
            {"name": "Base Color", "value": "_BaseColor"},
            {"name": "Metallic", "value": "_Metallic"},
            {"name": "Roughness", "value": "_Roughness"},
            {"name": "Normal", "value": "_Normal"},
            {"name": "Height", "value": "_Height"},
            {"name": "Specular Edge Color",
             "value": "_SpecularEdgeColor"},
            {"name": "Opacity", "value": "_Opacity"},
            {"name": "Displacement", "value": "_Displacement"},
            {"name": "Glossiness", "value": "_Glossiness"},
            {"name": "Anisotropy Level",
             "value": "_Anisotropylevel"},
            {"name": "Ambient Occlusion", "value": "_AO"},
            {"name": "Transmissive", "value": "_Transmissive"},
            {"name": "Reflection", "value": "_Reflection"},
            {"name": "Diffuse", "value": "_Diffuse"},
            {"name": "Index of Refraction", "value": "_Ior"},
            {"name": "Specular Level", "value": "_Specularlevel"},
            {"name": "Blending Mask", "value": "_BlendingMask"},
            {"name": "Translucency", "value": "_Translucency"},
            {"name": "Scattering", "value": "_Scattering"},
            {"name": "Scatter Color", "value": "_ScatterColor"},
            {"name": "Sheen Opacity", "value": "_SheenOpacity"},
            {"name": "Sheen Color", "value": "_SheenColor"},
            {"name": "Coat Opacity", "value": "_CoatOpacity"},
            {"name": "Coat Color", "value": "_CoatColor"},
            {"name": "Coat Roughness", "value": "_CoatRoughness"},
            {"name": "Coat Specular Level",
             "value": "_CoatSpecularLevel"},
            {"name": "Coat Normal", "value": "_CoatNormal"}
        ],
    }
}