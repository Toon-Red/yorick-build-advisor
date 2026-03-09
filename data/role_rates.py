"""Champion role probability rates for lane prediction.

Maps champion name -> {role: probability} for top/jungle/mid/bot/support.
Used to predict which enemy is most likely the top laner during champ select.
Probabilities sum to ~1.0 for each champion.
"""

ROLE_RATES: dict[str, dict[str, float]] = {
    "Aatrox":       {"top": 0.85, "jungle": 0.05, "mid": 0.08, "bot": 0.01, "support": 0.01},
    "Ahri":         {"top": 0.01, "jungle": 0.01, "mid": 0.95, "bot": 0.01, "support": 0.02},
    "Akali":        {"top": 0.25, "jungle": 0.01, "mid": 0.72, "bot": 0.01, "support": 0.01},
    "Akshan":       {"top": 0.10, "jungle": 0.01, "mid": 0.85, "bot": 0.03, "support": 0.01},
    "Alistar":      {"top": 0.01, "jungle": 0.01, "mid": 0.01, "bot": 0.01, "support": 0.96},
    "Ambessa":      {"top": 0.55, "jungle": 0.15, "mid": 0.25, "bot": 0.02, "support": 0.03},
    "Amumu":        {"top": 0.02, "jungle": 0.75, "mid": 0.01, "bot": 0.01, "support": 0.21},
    "Anivia":       {"top": 0.02, "jungle": 0.01, "mid": 0.93, "bot": 0.02, "support": 0.02},
    "Annie":        {"top": 0.02, "jungle": 0.01, "mid": 0.75, "bot": 0.02, "support": 0.20},
    "Aphelios":     {"top": 0.01, "jungle": 0.01, "mid": 0.01, "bot": 0.95, "support": 0.02},
    "Ashe":         {"top": 0.01, "jungle": 0.01, "mid": 0.01, "bot": 0.75, "support": 0.22},
    "Aurelion Sol": {"top": 0.01, "jungle": 0.01, "mid": 0.95, "bot": 0.02, "support": 0.01},
    "Aurora":       {"top": 0.30, "jungle": 0.02, "mid": 0.60, "bot": 0.02, "support": 0.06},
    "Azir":         {"top": 0.02, "jungle": 0.01, "mid": 0.95, "bot": 0.01, "support": 0.01},
    "Bard":         {"top": 0.01, "jungle": 0.01, "mid": 0.01, "bot": 0.01, "support": 0.96},
    "Bel'Veth":     {"top": 0.02, "jungle": 0.95, "mid": 0.01, "bot": 0.01, "support": 0.01},
    "Blitzcrank":   {"top": 0.01, "jungle": 0.01, "mid": 0.01, "bot": 0.01, "support": 0.96},
    "Brand":        {"top": 0.01, "jungle": 0.05, "mid": 0.15, "bot": 0.01, "support": 0.78},
    "Braum":        {"top": 0.01, "jungle": 0.01, "mid": 0.01, "bot": 0.01, "support": 0.96},
    "Briar":        {"top": 0.05, "jungle": 0.90, "mid": 0.03, "bot": 0.01, "support": 0.01},
    "Caitlyn":      {"top": 0.01, "jungle": 0.01, "mid": 0.02, "bot": 0.93, "support": 0.03},
    "Camille":      {"top": 0.85, "jungle": 0.05, "mid": 0.08, "bot": 0.01, "support": 0.01},
    "Cassiopeia":   {"top": 0.10, "jungle": 0.01, "mid": 0.85, "bot": 0.02, "support": 0.02},
    "Cho'Gath":     {"top": 0.70, "jungle": 0.05, "mid": 0.10, "bot": 0.01, "support": 0.14},
    "Corki":        {"top": 0.02, "jungle": 0.01, "mid": 0.90, "bot": 0.05, "support": 0.02},
    "Darius":       {"top": 0.90, "jungle": 0.05, "mid": 0.03, "bot": 0.01, "support": 0.01},
    "Diana":        {"top": 0.03, "jungle": 0.55, "mid": 0.40, "bot": 0.01, "support": 0.01},
    "Dr. Mundo":    {"top": 0.80, "jungle": 0.15, "mid": 0.02, "bot": 0.01, "support": 0.02},
    "Draven":       {"top": 0.01, "jungle": 0.01, "mid": 0.02, "bot": 0.94, "support": 0.02},
    "Ekko":         {"top": 0.03, "jungle": 0.45, "mid": 0.50, "bot": 0.01, "support": 0.01},
    "Elise":        {"top": 0.02, "jungle": 0.95, "mid": 0.01, "bot": 0.01, "support": 0.01},
    "Evelynn":      {"top": 0.01, "jungle": 0.96, "mid": 0.01, "bot": 0.01, "support": 0.01},
    "Ezreal":       {"top": 0.01, "jungle": 0.01, "mid": 0.03, "bot": 0.93, "support": 0.02},
    "Fiddlesticks": {"top": 0.02, "jungle": 0.85, "mid": 0.03, "bot": 0.01, "support": 0.09},
    "Fiora":        {"top": 0.95, "jungle": 0.01, "mid": 0.02, "bot": 0.01, "support": 0.01},
    "Fizz":         {"top": 0.05, "jungle": 0.02, "mid": 0.90, "bot": 0.01, "support": 0.02},
    "Galio":        {"top": 0.08, "jungle": 0.01, "mid": 0.70, "bot": 0.01, "support": 0.20},
    "Gangplank":    {"top": 0.75, "jungle": 0.01, "mid": 0.22, "bot": 0.01, "support": 0.01},
    "Garen":        {"top": 0.88, "jungle": 0.02, "mid": 0.08, "bot": 0.01, "support": 0.01},
    "Gnar":         {"top": 0.95, "jungle": 0.01, "mid": 0.02, "bot": 0.01, "support": 0.01},
    "Gragas":       {"top": 0.20, "jungle": 0.40, "mid": 0.15, "bot": 0.01, "support": 0.24},
    "Graves":       {"top": 0.08, "jungle": 0.80, "mid": 0.05, "bot": 0.05, "support": 0.02},
    "Gwen":         {"top": 0.85, "jungle": 0.08, "mid": 0.05, "bot": 0.01, "support": 0.01},
    "Hecarim":      {"top": 0.03, "jungle": 0.93, "mid": 0.02, "bot": 0.01, "support": 0.01},
    "Heimerdinger": {"top": 0.15, "jungle": 0.01, "mid": 0.35, "bot": 0.20, "support": 0.29},
    "Hwei":         {"top": 0.02, "jungle": 0.01, "mid": 0.65, "bot": 0.05, "support": 0.27},
    "Illaoi":       {"top": 0.95, "jungle": 0.01, "mid": 0.02, "bot": 0.01, "support": 0.01},
    "Irelia":       {"top": 0.45, "jungle": 0.01, "mid": 0.52, "bot": 0.01, "support": 0.01},
    "Ivern":        {"top": 0.01, "jungle": 0.93, "mid": 0.01, "bot": 0.01, "support": 0.04},
    "Janna":        {"top": 0.02, "jungle": 0.01, "mid": 0.01, "bot": 0.01, "support": 0.95},
    "Jarvan IV":    {"top": 0.10, "jungle": 0.80, "mid": 0.02, "bot": 0.01, "support": 0.07},
    "Jax":          {"top": 0.55, "jungle": 0.35, "mid": 0.08, "bot": 0.01, "support": 0.01},
    "Jayce":        {"top": 0.55, "jungle": 0.01, "mid": 0.42, "bot": 0.01, "support": 0.01},
    "Jhin":         {"top": 0.01, "jungle": 0.01, "mid": 0.02, "bot": 0.93, "support": 0.03},
    "Jinx":         {"top": 0.01, "jungle": 0.01, "mid": 0.02, "bot": 0.94, "support": 0.02},
    "K'Sante":      {"top": 0.93, "jungle": 0.02, "mid": 0.03, "bot": 0.01, "support": 0.01},
    "Kai'Sa":       {"top": 0.01, "jungle": 0.01, "mid": 0.03, "bot": 0.93, "support": 0.02},
    "Kalista":      {"top": 0.05, "jungle": 0.01, "mid": 0.01, "bot": 0.91, "support": 0.02},
    "Karma":        {"top": 0.05, "jungle": 0.01, "mid": 0.10, "bot": 0.01, "support": 0.83},
    "Karthus":      {"top": 0.02, "jungle": 0.55, "mid": 0.20, "bot": 0.20, "support": 0.03},
    "Kassadin":     {"top": 0.05, "jungle": 0.01, "mid": 0.92, "bot": 0.01, "support": 0.01},
    "Katarina":     {"top": 0.03, "jungle": 0.02, "mid": 0.92, "bot": 0.01, "support": 0.02},
    "Kayle":        {"top": 0.80, "jungle": 0.01, "mid": 0.15, "bot": 0.02, "support": 0.02},
    "Kayn":         {"top": 0.03, "jungle": 0.93, "mid": 0.02, "bot": 0.01, "support": 0.01},
    "Kennen":       {"top": 0.82, "jungle": 0.01, "mid": 0.10, "bot": 0.05, "support": 0.02},
    "Kha'Zix":      {"top": 0.02, "jungle": 0.93, "mid": 0.03, "bot": 0.01, "support": 0.01},
    "Kindred":      {"top": 0.02, "jungle": 0.88, "mid": 0.03, "bot": 0.05, "support": 0.02},
    "Kled":         {"top": 0.90, "jungle": 0.03, "mid": 0.05, "bot": 0.01, "support": 0.01},
    "Kog'Maw":      {"top": 0.01, "jungle": 0.01, "mid": 0.05, "bot": 0.88, "support": 0.05},
    "LeBlanc":      {"top": 0.02, "jungle": 0.01, "mid": 0.93, "bot": 0.01, "support": 0.03},
    "Lee Sin":      {"top": 0.08, "jungle": 0.85, "mid": 0.05, "bot": 0.01, "support": 0.01},
    "Leona":        {"top": 0.01, "jungle": 0.01, "mid": 0.01, "bot": 0.01, "support": 0.96},
    "Lillia":       {"top": 0.15, "jungle": 0.80, "mid": 0.03, "bot": 0.01, "support": 0.01},
    "Lissandra":    {"top": 0.10, "jungle": 0.01, "mid": 0.85, "bot": 0.01, "support": 0.03},
    "Lucian":       {"top": 0.03, "jungle": 0.01, "mid": 0.15, "bot": 0.78, "support": 0.03},
    "Lulu":         {"top": 0.02, "jungle": 0.01, "mid": 0.03, "bot": 0.02, "support": 0.92},
    "Lux":          {"top": 0.01, "jungle": 0.01, "mid": 0.35, "bot": 0.02, "support": 0.61},
    "Malphite":     {"top": 0.75, "jungle": 0.05, "mid": 0.05, "bot": 0.01, "support": 0.14},
    "Malzahar":     {"top": 0.02, "jungle": 0.01, "mid": 0.93, "bot": 0.02, "support": 0.02},
    "Maokai":       {"top": 0.15, "jungle": 0.30, "mid": 0.01, "bot": 0.01, "support": 0.53},
    "Master Yi":    {"top": 0.02, "jungle": 0.93, "mid": 0.03, "bot": 0.01, "support": 0.01},
    "Mel":          {"top": 0.02, "jungle": 0.01, "mid": 0.90, "bot": 0.05, "support": 0.02},
    "Milio":        {"top": 0.01, "jungle": 0.01, "mid": 0.01, "bot": 0.01, "support": 0.96},
    "Miss Fortune": {"top": 0.01, "jungle": 0.01, "mid": 0.02, "bot": 0.85, "support": 0.11},
    "Mordekaiser":  {"top": 0.82, "jungle": 0.10, "mid": 0.05, "bot": 0.01, "support": 0.02},
    "Morgana":      {"top": 0.02, "jungle": 0.05, "mid": 0.10, "bot": 0.01, "support": 0.82},
    "Naafiri":      {"top": 0.05, "jungle": 0.05, "mid": 0.87, "bot": 0.01, "support": 0.02},
    "Nami":         {"top": 0.01, "jungle": 0.01, "mid": 0.01, "bot": 0.01, "support": 0.96},
    "Nasus":        {"top": 0.90, "jungle": 0.03, "mid": 0.03, "bot": 0.01, "support": 0.03},
    "Nautilus":     {"top": 0.03, "jungle": 0.02, "mid": 0.01, "bot": 0.01, "support": 0.93},
    "Neeko":        {"top": 0.08, "jungle": 0.03, "mid": 0.40, "bot": 0.10, "support": 0.39},
    "Nidalee":      {"top": 0.03, "jungle": 0.90, "mid": 0.04, "bot": 0.01, "support": 0.02},
    "Nilah":        {"top": 0.01, "jungle": 0.01, "mid": 0.02, "bot": 0.93, "support": 0.03},
    "Nocturne":     {"top": 0.05, "jungle": 0.85, "mid": 0.05, "bot": 0.01, "support": 0.04},
    "Nunu & Willump": {"top": 0.02, "jungle": 0.92, "mid": 0.03, "bot": 0.01, "support": 0.02},
    "Olaf":         {"top": 0.45, "jungle": 0.50, "mid": 0.02, "bot": 0.01, "support": 0.02},
    "Orianna":      {"top": 0.01, "jungle": 0.01, "mid": 0.95, "bot": 0.01, "support": 0.02},
    "Ornn":         {"top": 0.93, "jungle": 0.02, "mid": 0.02, "bot": 0.01, "support": 0.02},
    "Pantheon":     {"top": 0.20, "jungle": 0.10, "mid": 0.35, "bot": 0.01, "support": 0.34},
    "Poppy":        {"top": 0.35, "jungle": 0.40, "mid": 0.02, "bot": 0.01, "support": 0.22},
    "Pyke":         {"top": 0.02, "jungle": 0.01, "mid": 0.10, "bot": 0.01, "support": 0.86},
    "Qiyana":       {"top": 0.02, "jungle": 0.05, "mid": 0.90, "bot": 0.01, "support": 0.02},
    "Quinn":        {"top": 0.85, "jungle": 0.02, "mid": 0.08, "bot": 0.03, "support": 0.02},
    "Rakan":        {"top": 0.01, "jungle": 0.01, "mid": 0.02, "bot": 0.01, "support": 0.95},
    "Rammus":       {"top": 0.03, "jungle": 0.93, "mid": 0.01, "bot": 0.01, "support": 0.02},
    "Rek'Sai":      {"top": 0.02, "jungle": 0.95, "mid": 0.01, "bot": 0.01, "support": 0.01},
    "Rell":         {"top": 0.01, "jungle": 0.02, "mid": 0.01, "bot": 0.01, "support": 0.95},
    "Renata Glasc": {"top": 0.01, "jungle": 0.01, "mid": 0.01, "bot": 0.01, "support": 0.96},
    "Renekton":     {"top": 0.88, "jungle": 0.03, "mid": 0.07, "bot": 0.01, "support": 0.01},
    "Rengar":       {"top": 0.20, "jungle": 0.75, "mid": 0.03, "bot": 0.01, "support": 0.01},
    "Riven":        {"top": 0.88, "jungle": 0.02, "mid": 0.08, "bot": 0.01, "support": 0.01},
    "Rumble":       {"top": 0.55, "jungle": 0.15, "mid": 0.28, "bot": 0.01, "support": 0.01},
    "Ryze":         {"top": 0.15, "jungle": 0.01, "mid": 0.80, "bot": 0.02, "support": 0.02},
    "Samira":       {"top": 0.01, "jungle": 0.01, "mid": 0.02, "bot": 0.94, "support": 0.02},
    "Sejuani":      {"top": 0.10, "jungle": 0.80, "mid": 0.02, "bot": 0.01, "support": 0.07},
    "Senna":        {"top": 0.01, "jungle": 0.01, "mid": 0.01, "bot": 0.30, "support": 0.67},
    "Seraphine":    {"top": 0.01, "jungle": 0.01, "mid": 0.15, "bot": 0.20, "support": 0.63},
    "Sett":         {"top": 0.55, "jungle": 0.10, "mid": 0.10, "bot": 0.01, "support": 0.24},
    "Shaco":        {"top": 0.02, "jungle": 0.75, "mid": 0.02, "bot": 0.01, "support": 0.20},
    "Shen":         {"top": 0.80, "jungle": 0.05, "mid": 0.01, "bot": 0.01, "support": 0.13},
    "Shyvana":      {"top": 0.10, "jungle": 0.85, "mid": 0.02, "bot": 0.01, "support": 0.02},
    "Singed":       {"top": 0.88, "jungle": 0.03, "mid": 0.05, "bot": 0.01, "support": 0.03},
    "Sion":         {"top": 0.65, "jungle": 0.05, "mid": 0.10, "bot": 0.01, "support": 0.19},
    "Sivir":        {"top": 0.01, "jungle": 0.01, "mid": 0.03, "bot": 0.93, "support": 0.02},
    "Skarner":      {"top": 0.10, "jungle": 0.80, "mid": 0.02, "bot": 0.01, "support": 0.07},
    "Smolder":      {"top": 0.05, "jungle": 0.01, "mid": 0.15, "bot": 0.77, "support": 0.02},
    "Sona":         {"top": 0.01, "jungle": 0.01, "mid": 0.02, "bot": 0.02, "support": 0.94},
    "Soraka":       {"top": 0.03, "jungle": 0.01, "mid": 0.02, "bot": 0.01, "support": 0.93},
    "Swain":        {"top": 0.08, "jungle": 0.01, "mid": 0.20, "bot": 0.15, "support": 0.56},
    "Sylas":        {"top": 0.10, "jungle": 0.08, "mid": 0.78, "bot": 0.01, "support": 0.03},
    "Syndra":       {"top": 0.01, "jungle": 0.01, "mid": 0.93, "bot": 0.03, "support": 0.02},
    "Tahm Kench":   {"top": 0.70, "jungle": 0.02, "mid": 0.02, "bot": 0.01, "support": 0.25},
    "Taliyah":      {"top": 0.02, "jungle": 0.30, "mid": 0.60, "bot": 0.03, "support": 0.05},
    "Talon":        {"top": 0.05, "jungle": 0.25, "mid": 0.67, "bot": 0.01, "support": 0.02},
    "Taric":        {"top": 0.05, "jungle": 0.02, "mid": 0.01, "bot": 0.01, "support": 0.91},
    "Teemo":        {"top": 0.75, "jungle": 0.05, "mid": 0.08, "bot": 0.05, "support": 0.07},
    "Thresh":       {"top": 0.01, "jungle": 0.01, "mid": 0.01, "bot": 0.01, "support": 0.96},
    "Tristana":     {"top": 0.03, "jungle": 0.01, "mid": 0.15, "bot": 0.78, "support": 0.03},
    "Trundle":      {"top": 0.30, "jungle": 0.50, "mid": 0.01, "bot": 0.01, "support": 0.18},
    "Tryndamere":   {"top": 0.80, "jungle": 0.03, "mid": 0.15, "bot": 0.01, "support": 0.01},
    "Twisted Fate": {"top": 0.03, "jungle": 0.01, "mid": 0.80, "bot": 0.10, "support": 0.06},
    "Twitch":       {"top": 0.01, "jungle": 0.05, "mid": 0.02, "bot": 0.82, "support": 0.10},
    "Udyr":         {"top": 0.20, "jungle": 0.75, "mid": 0.02, "bot": 0.01, "support": 0.02},
    "Urgot":        {"top": 0.90, "jungle": 0.02, "mid": 0.05, "bot": 0.02, "support": 0.01},
    "Varus":        {"top": 0.02, "jungle": 0.01, "mid": 0.10, "bot": 0.82, "support": 0.05},
    "Vayne":        {"top": 0.15, "jungle": 0.01, "mid": 0.02, "bot": 0.80, "support": 0.02},
    "Veigar":       {"top": 0.02, "jungle": 0.01, "mid": 0.65, "bot": 0.15, "support": 0.17},
    "Vel'Koz":      {"top": 0.01, "jungle": 0.01, "mid": 0.40, "bot": 0.02, "support": 0.56},
    "Vex":          {"top": 0.02, "jungle": 0.01, "mid": 0.92, "bot": 0.02, "support": 0.03},
    "Vi":           {"top": 0.03, "jungle": 0.92, "mid": 0.02, "bot": 0.01, "support": 0.02},
    "Viego":        {"top": 0.08, "jungle": 0.85, "mid": 0.05, "bot": 0.01, "support": 0.01},
    "Viktor":       {"top": 0.02, "jungle": 0.01, "mid": 0.93, "bot": 0.02, "support": 0.02},
    "Vladimir":     {"top": 0.15, "jungle": 0.01, "mid": 0.80, "bot": 0.02, "support": 0.02},
    "Volibear":     {"top": 0.50, "jungle": 0.45, "mid": 0.02, "bot": 0.01, "support": 0.02},
    "Warwick":      {"top": 0.20, "jungle": 0.75, "mid": 0.02, "bot": 0.01, "support": 0.02},
    "Wukong":       {"top": 0.35, "jungle": 0.55, "mid": 0.08, "bot": 0.01, "support": 0.01},
    "Xayah":        {"top": 0.01, "jungle": 0.01, "mid": 0.02, "bot": 0.94, "support": 0.02},
    "Xerath":       {"top": 0.01, "jungle": 0.01, "mid": 0.40, "bot": 0.02, "support": 0.56},
    "Xin Zhao":     {"top": 0.08, "jungle": 0.85, "mid": 0.03, "bot": 0.01, "support": 0.03},
    "Yasuo":        {"top": 0.10, "jungle": 0.01, "mid": 0.65, "bot": 0.22, "support": 0.02},
    "Yone":         {"top": 0.15, "jungle": 0.01, "mid": 0.70, "bot": 0.12, "support": 0.02},
    "Yorick":       {"top": 0.93, "jungle": 0.03, "mid": 0.02, "bot": 0.01, "support": 0.01},
    "Yunara":       {"top": 0.02, "jungle": 0.01, "mid": 0.02, "bot": 0.01, "support": 0.94},
    "Yuumi":        {"top": 0.01, "jungle": 0.01, "mid": 0.02, "bot": 0.01, "support": 0.95},
    "Zaahen":       {"top": 0.75, "jungle": 0.05, "mid": 0.15, "bot": 0.03, "support": 0.02},
    "Zac":          {"top": 0.10, "jungle": 0.82, "mid": 0.02, "bot": 0.01, "support": 0.05},
    "Zed":          {"top": 0.02, "jungle": 0.05, "mid": 0.90, "bot": 0.01, "support": 0.02},
    "Zeri":         {"top": 0.02, "jungle": 0.01, "mid": 0.05, "bot": 0.90, "support": 0.02},
    "Ziggs":        {"top": 0.01, "jungle": 0.01, "mid": 0.40, "bot": 0.40, "support": 0.18},
    "Zilean":       {"top": 0.02, "jungle": 0.01, "mid": 0.25, "bot": 0.01, "support": 0.71},
    "Zoe":          {"top": 0.01, "jungle": 0.01, "mid": 0.93, "bot": 0.02, "support": 0.03},
    "Zyra":         {"top": 0.02, "jungle": 0.02, "mid": 0.08, "bot": 0.01, "support": 0.87},
}


def get_top_probability(champion_name: str) -> float:
    """Return the probability that a champion is played top lane."""
    if champion_name in ROLE_RATES:
        return ROLE_RATES[champion_name].get("top", 0.0)
    return 0.20  # Unknown champion default


def get_role_probability(champion_name: str, role: str) -> float:
    """Return the probability that a champion is played in a given role."""
    if champion_name in ROLE_RATES:
        return ROLE_RATES[champion_name].get(role, 0.0)
    return 0.20  # Unknown champion default


def predict_roles(champion_names: list[str]) -> dict[str, str]:
    """Given a list of champion names, predict the most likely role assignment.

    Uses a greedy approach: assign the highest-probability (champion, role) pair
    first, then remove that champion and role from consideration.

    Returns dict mapping role -> champion_name.
    """
    roles = ["top", "jungle", "mid", "bot", "support"]
    # Build list of (probability, champion, role)
    candidates = []
    for champ in champion_names:
        rates = ROLE_RATES.get(champ, {r: 0.20 for r in roles})
        for role in roles:
            candidates.append((rates.get(role, 0.0), champ, role))

    candidates.sort(reverse=True)
    assigned_champs: set[str] = set()
    assigned_roles: set[str] = set()
    result: dict[str, str] = {}

    for prob, champ, role in candidates:
        if champ in assigned_champs or role in assigned_roles:
            continue
        result[role] = champ
        assigned_champs.add(champ)
        assigned_roles.add(role)
        if len(result) == len(roles):
            break

    return result
