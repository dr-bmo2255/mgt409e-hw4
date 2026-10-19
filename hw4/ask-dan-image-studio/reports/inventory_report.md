# Ask Dan Image Studio — Phase 0 inventory (dry run, no paid calls)

## Inputs
- **spec**: ASK_DAN_CLAUDE_CODE_IMAGE_STUDIO_SPEC.txt (sha256 787a01735ad3…)
- **dan_final_zip**: Dan Final Images(2).zip (sha256 e5943f3f7677…)
- **dan_refs_zip**: Dan Image References.zip (sha256 3167aab05e5d…)
- **catalogue_zip**: data 2.zip (sha256 33e059f34f23…)
- **audit_xlsx**: ask_dan_data2_audit.xlsx (sha256 a133b38fe6ee…)
- **checklist_txt**: ask_dan_data2_checklist.txt (sha256 dc469c1ede72…)

## Reconciled counts
| Metric | Studio (verified) | Previous audit |
|---|---|---|
| catalogue_products | 102 | 102 |
| dan_assets_required | 54 | 54 |
| existing_assets | 19 | 19 |
| missing_assets | 35 | 35 |
| product_photos_present | 102/102 | |
| shields_available | 31 | |
| dan_references | 5 | |

## Discrepancies vs previous audit
- `2025-yale-vs-harvard-t-shirt` — audit filename not found in archive: audit `Dan Harvard Sideeye.png` → studio `Dan Ivy Harvard Sideeye.png`
- `crew-left-chest-hoodie` — audit filename not found in archive: audit `Dan Harvard Crew Rowing.png` → studio `Dan Crew Rowing.png`

## Dan archive files
- Dan Baseball Babe Ruth.png — mapped → `dan_sport_baseball` (Not square)
- Dan Basketball Dunk.png — mapped → `dan_sport_basketball` (Not square)
- Dan Benjamin Franklin.png — mapped → `dan_college_benjamin_franklin` (College shield/lettering should be visually checked against references/shields)
- Dan Berkely College.png — mapped → `dan_college_berkeley` (Filename misspells Berkeley (kept as-is; mapped, not renamed); College shield/lettering should be visually checked against references/shields)
- Dan Branford.png — mapped → `dan_college_branford` (College shield/lettering should be visually checked against references/shields)
- Dan Crew Rowing.png — mapped → `dan_sport_rowing` (Not square)
- Dan Davenport.png — mapped → `dan_college_davenport` (College shield/lettering should be visually checked against references/shields)
- Dan Ezra Stiles.png — out_of_scope → `dan_college_ezra_stiles` (College shield/lettering should be visually checked against references/shields)
- Dan FootBall C.png — mapped → `dan_sport_football` (Below 1024px on one side (1042×732); Not square)
- Dan Football A.png — mapped → `dan_sport_football` (Not square)
- Dan Football B.png — mapped → `dan_sport_football` (Below 1024px on one side (1048×678); Not square)
- Dan Grace Hopper.png — mapped → `dan_college_grace_hopper` (College shield/lettering should be visually checked against references/shields)
- Dan Ice Hockey.png — mapped → `dan_sport_ice_hockey` (Not square)
- Dan Ivy Brown.png — out_of_scope → `dan_rival_brown` (Below 1024px on one side (1078×710); Not square)
- Dan Ivy Columbia.png — out_of_scope → `dan_rival_columbia` (Below 1024px on one side (1076×712); Not square)
- Dan Ivy Cornell.png — out_of_scope → `dan_rival_cornell` (Below 1024px on one side (1076×714); Not square)
- Dan Ivy Dartmouth.png — out_of_scope → `dan_rival_dartmouth` (Below 1024px on one side (1072×712); Not square)
- Dan Ivy Harvard Sideeye.png — mapped → `dan_rival_harvard` (Not square)
- Dan Ivy Princeton.png — out_of_scope → `dan_rival_princeton` (Not square)
- Dan Ivy UPenn.png — out_of_scope → `dan_rival_upenn` (Not square)
- Dan Jonathan Edwards.png — mapped → `dan_college_jonathan_edwards` (College shield/lettering should be visually checked against references/shields)
- Dan Morse.png — mapped → `dan_college_morse` (College shield/lettering should be visually checked against references/shields)
- Dan Pauli Murray.png — out_of_scope → `dan_college_pauli_murray` (College shield/lettering should be visually checked against references/shields)
- Dan Pierson.png — mapped → `dan_college_pierson` (College shield/lettering should be visually checked against references/shields)
- Dan Saybrook.png — mapped → `dan_college_saybrook` (College shield/lettering should be visually checked against references/shields)
- Dan Silliman.png — out_of_scope → `dan_college_silliman` (College shield/lettering should be visually checked against references/shields)
- Dan Soccer A.png — mapped → `dan_sport_soccer` (Below 1024px on one side (712×1406); Not square)
- Dan Soccer B.png — mapped → `dan_sport_soccer` (Below 1024px on one side (696×1410); Not square)
- Dan Soccer C.png — mapped → `dan_sport_soccer` (Below 1024px on one side (712×1426); Not square)
- Dan Socks and Hoodie.png — collage_excluded (Two-panel collage: not an individual asset)
- Dan Swimming.png — mapped → `dan_sport_swimming` (Not square)
- Dan Timothy Dwight.png — mapped → `dan_college_timothy_dwight` (College shield/lettering should be visually checked against references/shields)
- Dan Trumbull.png — mapped → `dan_college_trumbull` (College shield/lettering should be visually checked against references/shields)

## Generation queue (MISSING, catalogue-scoped)
- `dan_apparel_other.png` — Apparel: Other Apparel (1 product(s)); shield: —
- `dan_crewneck.png` — Apparel: Crewnecks (8 product(s)); shield: —
- **PILOT** `dan_hoodie.png` — Apparel: Hoodies (7 product(s)); shield: —
- `dan_jacket.png` — Apparel: Jackets / Full-Zips (1 product(s)); shield: —
- `dan_performance.png` — Apparel: Performance Apparel (2 product(s)); shield: —
- `dan_tshirt.png` — Apparel: T-Shirts (4 product(s)); shield: —
- `dan_family_aunt.png` — Family: Aunt (1 product(s)); shield: —
- `dan_family_brother.png` — Family: Brother (1 product(s)); shield: —
- `dan_family_cousin.png` — Family: Cousin (1 product(s)); shield: —
- `dan_family_dad.png` — Family: Dad (3 product(s)); shield: —
- `dan_family_grandma.png` — Family: Grandma (1 product(s)); shield: —
- `dan_family_grandpa.png` — Family: Grandpa (2 product(s)); shield: —
- `dan_family_mom.png` — Family: Mom (2 product(s)); shield: —
- `dan_family_uncle.png` — Family: Uncle (1 product(s)); shield: —
- `dan_school_architecture.png` — Schools: Architecture (2 product(s)); shield: school_of_architecture
- `dan_school_art.png` — Schools: Art (2 product(s)); shield: school_of_art
- `dan_school_divinity.png` — Schools: Divinity (1 product(s)); shield: divinity_school
- `dan_school_engineering_and_applied_science.png` — Schools: Engineering & Applied Science (1 product(s)); shield: school_of_engineering_and_applied_science
- `dan_school_environment.png` — Schools: Environment (1 product(s)); shield: school_of_the_environment
- `dan_school_law.png` — Schools: Law (1 product(s)); shield: law_school
- **PILOT** `dan_school_management.png` — Schools: Management (1 product(s)); shield: school_of_management
- `dan_school_medicine.png` — Schools: Medicine (1 product(s)); shield: school_of_medicine
- `dan_school_music.png` — Schools: Music (1 product(s)); shield: school_of_music
- `dan_school_nursing.png` — Schools: Nursing (1 product(s)); shield: school_of_nursing
- `dan_school_public_health.png` — Schools: Public Health (1 product(s)); shield: school_of_public_health
- `dan_sport_diving.png` — Sports: Diving (3 product(s)); shield: —
- `dan_sport_fencing.png` — Sports: Fencing (1 product(s)); shield: —
- `dan_sport_field_hockey.png` — Sports: Field Hockey (2 product(s)); shield: —
- `dan_sport_golf.png` — Sports: Golf (2 product(s)); shield: —
- **PILOT** `dan_sport_lacrosse.png` — Sports: Lacrosse (1 product(s)); shield: —
- `dan_sport_sailing.png` — Sports: Sailing (1 product(s)); shield: —
- `dan_sport_squash.png` — Sports: Squash (2 product(s)); shield: —
- `dan_sport_tennis.png` — Sports: Tennis (2 product(s)); shield: —
- `dan_sport_track_and_field.png` — Sports: Track & Field (2 product(s)); shield: —
- `dan_sport_volleyball.png` — Sports: Volleyball (2 product(s)); shield: —
