# Exercise media licenses

## ExerciseDB.io assets

- Provider and attribution: ExerciseDB.io.
- Storage: only project-owner-supplied local package files are copied into the application.
- License requirement: a valid ExerciseDB.io license or other applicable permission must be held by the project owner before import and deployment.
- Importer behavior: no scraping, downloading, or external request is performed, and the importer does not claim or fabricate license terms.

The repository's `sample-set/` contains the owner-supplied `0025` Barbell Bench Press example used by the local importer. Adding the full catalog requires placing the licensed package on disk and running the same importer.

## Source evaluation (August 29, 2026)

The product requirement is one consistent anatomical character for every active GymAI exercise. Sources were evaluated for visual consistency, animation coverage, self-hosting, and production reuse rights.

| Source | Coverage and consistency | Production reuse | Decision |
| --- | --- | --- | --- |
| ExerciseDB.io Starter / Pro | 1,394 matching same-character GIFs; Starter includes 180/360, Pro adds 720/1080 | Permitted inside a product after purchase; raw redistribution prohibited | **Approved and exact visual match.** Use the local importer with a project-owner-supplied licensed ZIP. |
| Public ExerciseDB/Gym Visual GitHub mirrors | Some mirrors contain 1,324 copied GIFs | Mirror notices require the original media license or prohibit commercial use | **Rejected.** Do not copy, scrape, or deploy these files. |
| Vital Animations | 400, 800+, or 1,500+ consistent HD MP4 animations depending on package | Advertised one-time commercial license and self-hosting; paid package required for broad coverage | **Possible alternative, not an exact character match.** Requires purchasing a package and a reviewed GymAI mapping. Do not mix its character with ExerciseDB media. |
| Vital Animations Free50 | 50 gym MP4s using the same male 3D character; 44 conservatively mapped to GymAI | Vendor free-pack license permits commercial in-app use and self-hosting | **Integrated as a lightweight alternative sample.** It proves the import/player path but does not satisfy all-exercise coverage. |
| Free Exercise DB | 876 paired still-photo exercises; 873 exact GymAI name matches | Unlicense / public domain | **Rejected for display.** Inspection found different real actors and gym backgrounds, so it violates the one-character requirement. |
| FitGif | Advertises 1,300+ GIFs and two consistent performers | API account required; free plan is a generic subset and returns expiring signed URLs | **Not imported.** No project API key and no self-hosted/permanent media URLs. |
| MuscleWiki API | 1,900+ exercises with male/female video | Paid API plan required for commercial use; media cannot be stored offline | **Not imported.** Requires project billing credentials and a runtime API dependency. |
| YMove | 1,068+ real-person HD videos with mostly consistent white background | Paid API; self-hosting is a separate license | **Not imported.** Different visual style and no project API key/license. |
| MoveKit | 412 consistent-mannequin MP4s | Paid downloadable packs with commercial license | **Insufficient coverage.** Its complete pack cannot cover 943 GymAI exercises. |
| wger | Open exercise data and individually licensed images | License varies by contributed media | **Rejected for this requirement.** It is not a same-character animation library. |
| MakeHuman / Z-Anatomy / BodyParts3D | Reusable character or anatomy building blocks, not a catalog of exercise movements | Open licenses vary by project | **Not a ready media source.** Producing and reviewing 943 equipment-aware animations would be a separate 3D production project. |

The approved route for the reference look is therefore the official ExerciseDB.io package. Finding copied GIF files on a public repository does not grant GymAI the right to ship them.

## Vital Animations package import

The official Free50 ZIP was downloaded from `https://vitalanimations.com/VitalAnimations.zip`. Its reviewed mapping intentionally omits six ambiguous or duplicate movements. Imported source clips are transcoded from 1080p to muted, fast-start 720p H.264 MP4 and receive a WebP poster; the resulting 44 animations occupy about 8.6 MB rather than shipping the 282 MB source ZIP.

```powershell
python backend/scripts/import_vital_animations_media.py --source <VitalAnimations.zip> --dry-run
python backend/scripts/import_vital_animations_media.py --source <VitalAnimations.zip>
python backend/scripts/verify_exercise_media_coverage.py --provider "Vital Animations" --media-type video --allow-incomplete
```

The importer also accepts a paid extracted package using the same JSON/MP4 ID convention. `backend/scripts/vital-animations-free50-mapping.json` is a reviewed source-ID-to-GymAI-name map; a larger licensed package will require expanding that map where names do not match exactly.

## Retired GymAI procedural media

The former low-poly `GymAI Visual Pipeline` records are deprecated and non-primary. The frontend excludes that provider and deprecated/rejected/failed statuses. Those files are not an approved visual source and must not be re-registered for user-facing display.
