# Holdout sourcing and v7 readiness: second access round

Owner: OpenAI Codex. Updated: 2026-10-08. Status: IN_PROGRESS overall;
this bounded access/pilot milestone is complete. No holdout admission or v7 launch.
User authorizes continuous preparation until v7 can train, stopping before training.

## Decisions from acquired content

- **MultiNatSmoke public access works.** Pinned Hugging Face revision
  `5b7a4e0f7a094d7e27381a5154ad71be99f58137`, archive43,677,465,490bytes;
  strict HTTP206 ranges and ZIP CRC checks, no full download. Inventory163,565
  members acquired using28,054,648bytes. Seed48 selected four Boreal and four
  AuSmoke image/mask pairs before retrieval. All eight decode, image/mask dimensions
  match, binary0/255 masks. Semantic masks produce1–168 connected components:
  components are **not accepted object boxes**. No automatic mask-to-box admission.
  Original Boreal boxed annotations were not recovered through this package.
- Visual review of all eight shows outdoor wildfire plumes. Boreal provenance
  remains four2022 burn events; the2026 mirror does not reset that age. AuSmoke
  paper describes original Australian burns and distant handheld/PTZ cameras;
  filename dates include2024. Event mapping remains unfinished. These may supply
  smoke stress evidence, not proof of indoor smoke coverage. Fire/person unknown.
- **AGHRI paired access works.** Original Figshare article32982638, published
  2026-08-21, CC BY4.0, source recording dates2024. Part6 inventory23,304members
  via4,239,769bytes; no complete10.6GB archive. Four seed48 sessions, complete
  ZED annotation JSONs, then three frozen random frames/session:12images/22boxes.
  Creator exporter confirms top-left xywh and numeric identities as person.
  All images decode; three images contain source boxes extending outside the image.
  No clipping/conversion yet. All12 overlays reviewed: greenhouse floor-level
  robot viewpoint, partial people/occlusion. Eligible supplemental person candidate;
  not room/doorway/high-mounted camera evidence. Section/instance names must be
  consolidated into original capture families; no31/65-group independence claim.
- **FURG bounded legacy fallback failed independent fire admission.** Recent
  alternatives have reuse/access/session problems; MultiNatSmoke and AGHRI do not
  supply boxed indoor fire. This reason was frozen before the old-source pilot.
  Two original pinned videos89,414,345bytes; case2_house904decoded frames versus
  907XML entries, negative341versus342, both29.97fps versus XML29. Dimensions match;
  no missing XML for decoded frames. Never materialize nonexistent tail frames.
  Audited43previews at30-frame spacing, with actual timestamps; not exactly1second.
  Five near pairs visually confirm **case2_house reuses inspected rawv32 scenes**.
  Reject that entire event, not just matched frames. Other FURG events unproven.
  Negative clip is an indoor exhibition from a moving low camera; final three
  previews are title graphics. XML annotation date2014 and end slate2012 show this
  fallback is older than2015–2017 metadata summaries suggested, not recent data.

## Independence probe and remaining requirements

Refreshed all33,849 corpus image SHA256 values against the existing registry;
joint-v4 split hashes unchanged. On63pilot images, exact0 and dHash<=5 candidates5,
all from case2_house versus inspectedv32. All five reviewed as shared scenes.
No candidate for these limited AGHRI/MultiNatSmoke pilots; this is not an exhaustive
crop/mirror/source-wide independence proof. No predictions or training occurred.

Planning targets remain unchanged:30independent groups, two sources,300fire/
300smoke/500person boxes and200verified negatives/class. **Still unmet.**
No class-negative scope is inferred from missing source labels. No automatic
expansion into previously rejected sources. No reopening the historical v6 test.

## Public metadata candidates and access limits

- [IndoorCrowd creator](https://sheepseb.github.io/IndoorCrowd/) and
  [Hugging Face](https://huggingface.co/datasets/sebnae/IndoorCrowd):2026 indoor
  source, promising human control subset. API gated=auto; original card request401.
  Access requires contact disclosure/terms. No account acceptance or bypass.
- [WEPDTOF](https://vip.bu.edu/projects/vsns/cossy/datasets/wepdtof/) and
  [FRIDA](https://vip.bu.edu/projects/vsns/cossy/datasets/frida/):2022 releases,
  indoor fisheye scenes, forms require name/institution/email. WEPDTOF has excluded
  peripheral ROI; FRIDA synchronized segments cannot be counted as separate scenes.
  No form submission; direct HTTP403 while public pages are web-readable.
- [UniData](https://github.com/UniData-pro/fire-and-smoke-dataset):limited preview,
  full source paid/contact-only, no purchase/contact.
- [GWFP paper](https://arxiv.org/html/2606.10174v1):classification/patch protocol,
  public release promised upon acceptance; not verified ready box GT.
- [SmokeBench](https://github.com/QianfengY/SmokeBench):desmoking image pairs,
  not yet verified person/fire/smoke boxes. No admission.

## Readiness probe and immediate continuation

Checkpoint SHA remains103b45ab6a61f2431b462ee2bc4402f6ddaa7b982e872afd50515e3c6ef28729.
Draft config SHA5cccddd70d70aef20f5adf2a5e53eee1b8ac1cf45e616fed475e8b93da0c7466;
run target absent. CUDA available on RTX5070Laptop8GB, approximately7.35GB free
at probe; available RAM19.26GB, E:free534.76GB. These are transient readings,
**not training peak-memory readiness**. No v7 train launched.

Next assess THUD++ original public Zenodo RGB-D release18459791 for real indoor
person boxes, then smart-factory2024 original inside/outside VOC archive access.
Reserve whole new sources, freeze bounded pilots before images, audit box semantics,
capture families/overlap/completeness. Revisit source-mask conversion only under an
explicit object convention. Freeze accepted holdout and evaluation policy before
final data/checkpoint/environment/resource readiness. V7 remains PLANNED.

Evidence and reproducible standard-library/OpenCV recipes:
`E:/HomeAssistantPi4/reports/indoor-readiness-sourcing-v2`.
Raw pilots: `E:/HomeAssistantPi4/raw/holdout-candidates/` under
`multinat-pilot-v1`, `aghri-pilot-v1`, `furg-video-pilot-v1`.
No dependency changes or secret reads. Earlier bound source reports stay immutable.

Primary metadata: [MultiNatSmoke creator](https://github.com/henryzhao0615/MultiNatSmoke),
[paper](https://arxiv.org/abs/2604.23542),
[AGHRI creator](https://github.com/LCAS/AGHRI-dataset-tools),
[original article API](https://api.figshare.com/v2/articles/32982638),
[FURG pinned source](https://github.com/steffensbola/furg-fire-dataset/tree/6aff09d7baa27425f31d1df685284c26cbffe7af).
