# Unity Project Scan Rules

Use these rules when scanning Unity projects for an agent knowledge base.

## Goals

- Create a compact navigation layer for future agents.
- Prefer path-level summaries over full source copying.
- Identify likely systems, entry points, configs, scenes, and open questions.
- Keep auto-generated claims at `confidence: medium` until verified.

## High-Signal Paths

Scan these paths by default when they exist:

- `Assets/Scripts/`
- `Assets/Editor/`
- `Assets/Resources/`
- `Assets/StreamingAssets/`
- `Assets/**/Config*/`
- `Assets/**/Data*/`
- `Packages/manifest.json`
- `Packages/packages-lock.json`
- `ProjectSettings/`
- `*.asmdef`
- `*.asmref`

## Low-Signal or Noisy Paths

Ignore these unless the user is debugging a specific issue that requires them:

- `Library/`
- `Temp/`
- `Logs/`
- `Builds/`
- `Obj/`
- `UserSettings/`
- `MemoryCaptures/`
- generated IDE files such as `.csproj` and `.sln`
- binary or large imported assets

## Binary Asset Extensions

Treat these as path-only signals by default:

- images: `.png`, `.jpg`, `.jpeg`, `.psd`, `.tga`, `.tif`, `.tiff`, `.webp`, `.exr`
- audio: `.wav`, `.mp3`, `.ogg`, `.aiff`, `.flac`
- video: `.mp4`, `.mov`, `.webm`, `.avi`
- models: `.fbx`, `.blend`, `.obj`, `.dae`, `.max`, `.ma`, `.mb`
- builds and archives: `.apk`, `.aab`, `.ipa`, `.zip`, `.7z`, `.rar`, `.dmg`
- fonts and binary blobs: `.ttf`, `.otf`, `.bytes`, `.dll`, `.so`, `.bundle`

## C# Summary Rules

For `.cs` files, extract structure instead of copying implementation:

- namespace
- class, interface, struct, and enum names
- inheritance hints, especially `MonoBehaviour`, `ScriptableObject`, and editor types
- Unity lifecycle methods such as `Awake`, `Start`, `OnEnable`, `Update`, and `OnDestroy`
- public methods
- serialized fields and attributes
- likely module from path and naming

## Roadmap Confidence

Static scans are useful for navigation, but not proof. Mark generated roadmap pages as:

```yaml
confidence: medium
```

Upgrade a topic to `confidence: high` only after an agent verifies the relevant source files and, when needed, scene, prefab, ScriptableObject, or config references.
