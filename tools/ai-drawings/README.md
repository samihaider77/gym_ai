# GymAI drawings: nayi exercises usi style mein

Yeh tool library jaisi black-ink drawings banata hai (Everkinetic style), un exercises ke liye jin ki tasveer
nahi hai. Har exercise ka start aur end pose pehle se likha hua hai (`exercise-poses.json`), is liye **koi video
ya clip record nahi karni**. Drawings Kaggle par free GPU se banti hain. App mein aane ke baad unhein chalane ke
liye internet ya GPU nahi chahiye.

## Is folder mein kya hai

| File | Kaam |
|---|---|
| `everkinetic-style.zip` | Training data: ~530 asal drawings (start/end) aur captions. Kaggle par upload karein. |
| `gymai_drawings.ipynb` | Kaggle notebook. Style seekhta hai, likhe hue poses se drawings banata hai. |
| `exercise-poses.json` | Har exercise ka likha hua start/end pose (notebook ke andar bhi shamil hai). |
| `POSES.md` | Pose likhne ka tareeqa, agar koi pose theek karna ho. |
| `exercises-without-drawing.txt` | Woh exercises jin ki drawing nahi, muscle ke hisaab se. |
| `pipeline.py` | Notebook ka asal code. |
| `build_dataset.py`, `make_notebook.py` | Zip aur notebook dobara banane ke liye. |

## Qadam ba qadam

### 1. Kaggle par ek dafa ki tayyari

1. kaggle.com par free account banayein aur **phone number verify** karein (warna GPU aur internet nahi milta).
2. **Datasets → New Dataset**: `everkinetic-style.zip` upload karein, naam `everkinetic-style` rakhein.

### 2. Notebook chalayein

1. **Code → New Notebook → File → Import Notebook**: `gymai_drawings.ipynb` chunein.
2. Right panel: **Accelerator → GPU T4 x2** (P100 nahi), aur **Internet → On**.
3. **+ Add Input** se `everkinetic-style` dataset jorein.
4. **Run All**. Pehli dafa style seekhne mein ~1 ghanta lagta hai, phir pehli 20 exercises banti hain.
5. Aakhir mein `review.png` dikhega (har exercise ke 2 options). Output panel se **gymai-drawings.zip** aur
   **gymai-style-lora.zip** download karein.

Quality theek lage to `LIMIT = 0` kar ke dobara chalayein: saari ~940 exercises banengi (~3-4 ghante).
`gymai-style-lora.zip` ko dataset bana kar input mein jor dein to training dobara nahi hogi.

### 3. App mein daalein (is PC par)

`backend` folder se:

```
.venv\Scripts\python.exe scripts\import_generated_drawings.py C:\path\gymai-drawings.zip --dry-run
.venv\Scripts\python.exe scripts\import_generated_drawings.py C:\path\gymai-drawings.zip
```

Default mein har exercise ka option 1 lagta hai. Agar `review.png` mein option 2 behtar ho, ya koi drawing
chhorni ho, to ek `picks.json` banayein aur `--pick picks.json` dein:

```json
{"Glute Bridge": 2, "Kettlebell Swing": 0}
```

(`0` = yeh exercise chhor do.)

### Optional: video se pose

Kisi exercise ka likha hua pose theek na bane to us ki chhoti clip (`Glute Bridge.mp4`, ya
`Glute Bridge__start.jpg` + `Glute Bridge__end.jpg`) ek doosre dataset mein daal kar input mein jor dein.
Notebook us exercise ke liye clip ka pose istemal karega. Yeh zaroori nahi.

## License

Asal drawings Everkinetic ki hain (CC BY-SA 4.0). Nayi drawings unhi se seekh kar bani hain, is liye har nayi
drawing par bhi CC BY-SA 4.0 aur Everkinetic ka credit app mein dikhaya jata hai.

## GPU

| GPU | Kya ho sakta hai |
|---|---|
| Kaggle T4 (free) | Sab kuch. Recommended. (P100 mat chunein, naya torch use nahi chalata.) |
| Apna NVIDIA 6-8 GB | Training aur drawings dono. |
| Apna NVIDIA 4 GB | Drawings theek; training mushkil (batch 1, zyada waqt). |
| 2 GB / Intel graphics | Practical nahi. |
