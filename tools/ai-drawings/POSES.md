# Writing exercise poses (exercise-poses.json)

`pipeline.py specposes` turns each written pose into an OpenPose skeleton, which the drawing model follows.
One entry per exercise:

```json
{"name": "Glute Bridge", "view": "side", "prompt": "lying on his back on the floor, knees bent, feet flat",
 "start": {"torso": 180, "head": 180, "arms": [[0, 0], [0, 0]], "legs": [[60, -60], [60, -60]]},
 "end":   {"torso": 200, "head": 200, "arms": [[0, 0], [0, 0]], "legs": [[20, -50], [20, -50]]}}
```

- `name`: exactly the app's English exercise name.
- `view`: `"side"` (person faces the picture's right) or `"front"` (person faces the viewer). Use front only when
  the movement happens sideways (lateral raises, jumping jacks, side bends); otherwise side.
- `prompt`: short scene detail the skeleton cannot show: body position and equipment, e.g.
  `"lying on a flat bench, holding a barbell above the chest"`. No exercise name, no style words.
- `start` / `end`: the two positions of one rep (start = beginning/rest, end = peak of the movement).

## Angles

Every segment has an angle in degrees, measured in the picture: `0` = pointing to the picture's right (the way a
side-view person faces), `90` = straight up, `-90` = straight down, `180` = pointing to the picture's left (behind).
Each segment starts where the previous one ends:

- `torso`: from the hips to the neck. Standing = 90. Lying on the back with the head on the left = 180.
- `head` (optional, defaults to the torso angle): from the neck to the top of the head.
- `arms`: `[[upper arm, forearm], [upper arm, forearm]]`: shoulder→elbow, then elbow→wrist.
- `legs`: `[[thigh, shin], [thigh, shin]]`: hip→knee, then knee→ankle.
- `face` (optional): `"up"`, `"down"`, `"left"` or `"right"`, the way the face points. By default the face is on the
  front of the head (for a standing side view: right). Set it for face-down positions (e.g. lying face down: `"down"`).

Side view: the first arm/leg is the one nearer the viewer. Front view: the first is on the picture's left.
Body proportions (fraction of height): torso 0.30, head 0.11, upper arm 0.165, forearm 0.15, thigh 0.245, shin 0.245.
Use these to keep hands and feet on the floor or bench where they belong.

## Reference poses (side view)

| Position | Values |
|---|---|
| Standing, arms down | torso 90, arms [[-90,-90],[-90,-90]], legs [[-90,-90],[-90,-90]] |
| Sitting on a bench | torso 90, legs [[0,-90],[0,-90]] |
| Lying on the back (head left) | torso 180, head 180, legs [[0,0],[0,0]] |
| Lying face down (head right) | torso 0, head 0, face "down", legs [[180,180],[180,180]] |
| Plank / push-up top | torso 23, arms [[-90,-90],[-90,-90]], legs [[203,203],[203,203]] |
| Bottom of a squat | torso 65, head 80, legs [[5,-110],[5,-110]] |
| Hip hinge (deadlift, bent-over row) | torso 20, head 30, legs [[-80,-95],[-80,-95]] |
| Lunge | torso 90, legs [[-40,-90],[-130,-160]] |
| Hanging from a bar | torso 90, arms [[90,90],[90,90]], legs [[-90,-90],[-90,-90]] |
| Bicep curl top | arms [[-95,75],[-92,78]] |
| Arms overhead | arms [[88,90],[90,90]] |
| Kneeling (on both knees) | torso 90, legs [[-90,180],[-90,180]] |
| Front view, arms out to the sides | arms [[178,172],[2,8]] |
