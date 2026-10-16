"""Free tools: the pieces that are more than text.

The pages are still written as text files in blog-src/ (page-irl.en.md and so on). A line such as
{{irl-form}} in one of them is replaced here by the form, the calendar, the table or the links.
Nothing on these pages is sent to a server: the calculator runs in the browser (irl.js).
"""
import datetime, html, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHECKED = "2026-10-16"   # the day the facts below were last checked against their sources
MONTHS = {"en": ["January","February","March","April","May","June","July","August","September","October","November","December"],
          "fr": ["janvier","février","mars","avril","mai","juin","juillet","août","septembre","octobre","novembre","décembre"]}
def esc(s): return html.escape(s, quote=True)
def fdate(iso, lang):
    d = datetime.date.fromisoformat(iso); m = MONTHS[lang][d.month - 1]
    return (f"{d.day} {m} {d.year}" if lang == "en" else (("1er" if d.day == 1 else str(d.day)) + f" {m} {d.year}"))

# ------------------------------------------------------------------ the calculator
UI = {
    "en": dict(rent="Current monthly rent, excluding charges", rent_hint="In euros, for example 600 or 600.50.",
               quarter="Reference quarter in your lease", quarter_hint="The IRL quarter your lease names. If it names none, the last index published when the lease was signed.",
               date="Revision date", date_hint="Optional. The anniversary of the lease, or the date the lease sets. Used to show your deadline.",
               dpe="Energy label (DPE)", dpe_hint="A home rated F or G cannot have its rent revised.", dpe_none="I don't know / not rated",
               go="Calculate the new rent", noscript="This calculator needs JavaScript. The latest index values are listed below, and the formula is explained on this page.",
               latest="Latest published values", q="Quarter", v="IRL", asof="Figures as of"),
    "fr": dict(rent="Loyer mensuel actuel, hors charges", rent_hint="En euros, par exemple 600 ou 600,50.",
               quarter="Trimestre de référence de votre bail", quarter_hint="Le trimestre de l'IRL indiqué dans le bail. À défaut, le dernier indice publié à la signature du bail.",
               date="Date de révision", date_hint="Facultatif. L'anniversaire du bail, ou la date prévue par le bail. Sert à afficher votre échéance.",
               dpe="Étiquette énergie (DPE)", dpe_hint="Un logement classé F ou G ne peut pas voir son loyer révisé.", dpe_none="Je ne sais pas / non classé",
               go="Calculer le nouveau loyer", noscript="Ce calculateur a besoin de JavaScript. Les derniers indices sont listés plus bas, et la formule est expliquée sur cette page.",
               latest="Derniers indices publiés", q="Trimestre", v="IRL", asof="Chiffres au"),
}
def irl_form(lang):
    u = UI[lang]
    def field(fid, label, hint, control):
        return (f'<div class="form-field"><label for="{fid}">{esc(label)}</label>{control}'
                f'<p class="form-note" id="{fid}-hint">{esc(hint)}</p><p class="tool-err" id="{fid}-err" role="alert" hidden></p></div>')
    dpe = "".join(f'<option value="{c}">{c}</option>' for c in "ABCDEFG")
    return f'''<div class="form-card tool-card">
<form id="irl-form" novalidate>
{field("irl-rent", u["rent"], u["rent_hint"], '<input type="text" id="irl-rent" name="rent" inputmode="decimal" autocomplete="off" aria-describedby="irl-rent-hint irl-rent-err">')}
{field("irl-quarter", u["quarter"], u["quarter_hint"], '<select id="irl-quarter" name="quarter" aria-describedby="irl-quarter-hint irl-quarter-err"></select>')}
<div class="form-row">
{field("irl-date", u["date"], u["date_hint"], '<input type="date" id="irl-date" name="date" aria-describedby="irl-date-hint irl-date-err">')}
{field("irl-dpe", u["dpe"], u["dpe_hint"], f'<select id="irl-dpe" name="dpe" aria-describedby="irl-dpe-hint"><option value="">{esc(u["dpe_none"])}</option>{dpe}</select>')}
</div>
<button type="submit" class="btn btn-primary" style="width:100%;">{esc(u["go"])}</button>
</form>
<div id="irl-result" class="tool-result" role="status" aria-live="polite"></div>
<noscript><p class="form-note">{esc(u["noscript"])}</p></noscript>
</div>'''

DEPUI = {
    "en": dict(keys="Date the tenant handed back the keys", keys_hint="In person or by registered letter. The deadline runs from this day.",
               inv="Exit inventory", inv_hint="Compared with the entry inventory.", inv_pick="Choose…", inv_match="Matches the entry inventory", inv_differs="Differs from the entry inventory",
               rent="Monthly rent, excluding charges", rent_hint="In euros, for example 600 or 600.50. Used for the late penalty.",
               check="Date the deposit is or was returned", check_hint="Optional. Leave empty to use today.",
               noaddr="The tenant has not given a new address", go="Work out the deadline and any penalty",
               noscript="This calculator needs JavaScript. The rules are explained on this page."),
    "fr": dict(keys="Date de remise des clés par le locataire", keys_hint="En main propre ou par lettre recommandée. Le délai court à partir de ce jour.",
               inv="État des lieux de sortie", inv_hint="Comparé à l'état des lieux d'entrée.", inv_pick="Choisir…", inv_match="Conforme à l'état des lieux d'entrée", inv_differs="Différent de l'état des lieux d'entrée",
               rent="Loyer mensuel, hors charges", rent_hint="En euros, par exemple 600 ou 600,50. Sert à calculer la pénalité de retard.",
               check="Date à laquelle le dépôt est ou a été rendu", check_hint="Facultatif. Laissez vide pour utiliser aujourd'hui.",
               noaddr="Le locataire n'a pas donné sa nouvelle adresse", go="Calculer le délai et la pénalité éventuelle",
               noscript="Ce calculateur a besoin de JavaScript. Les règles sont expliquées sur cette page."),
}
def deposit_form(lang):
    u = DEPUI[lang]
    def field(fid, label, hint, control):
        return (f'<div class="form-field"><label for="{fid}">{esc(label)}</label>{control}'
                f'<p class="form-note" id="{fid}-hint">{esc(hint)}</p><p class="tool-err" id="{fid}-err" role="alert" hidden></p></div>')
    return f'''<div class="form-card tool-card">
<form id="dep-form" novalidate>
{field("dep-keys", u["keys"], u["keys_hint"], '<input type="date" id="dep-keys" name="keys" aria-describedby="dep-keys-hint dep-keys-err">')}
{field("dep-inv", u["inv"], u["inv_hint"], f'<select id="dep-inv" name="inventory" aria-describedby="dep-inv-hint dep-inv-err"><option value="">{esc(u["inv_pick"])}</option><option value="match">{esc(u["inv_match"])}</option><option value="differs">{esc(u["inv_differs"])}</option></select>')}
<div class="form-row">
{field("dep-rent", u["rent"], u["rent_hint"], '<input type="text" id="dep-rent" name="rent" inputmode="decimal" autocomplete="off" aria-describedby="dep-rent-hint dep-rent-err">')}
{field("dep-check", u["check"], u["check_hint"], '<input type="date" id="dep-check" name="check" aria-describedby="dep-check-hint dep-check-err">')}
</div>
<div class="form-check"><input type="checkbox" id="dep-noaddr" name="noaddr"><label for="dep-noaddr">{esc(u["noaddr"])}</label></div>
<button type="submit" class="btn btn-primary" style="width:100%;">{esc(u["go"])}</button>
</form>
<div id="dep-result" class="tool-result" role="status" aria-live="polite"></div>
<noscript><p class="form-note">{esc(u["noscript"])}</p></noscript>
</div>'''

def irl_table(lang):
    u = UI[lang]
    series = json.load(open(os.path.join(ROOT, "tools", "irl-series.json")))
    keys = sorted(series, reverse=True)[:12]
    lab = (lambda k: k.replace("-Q", " Q")) if lang == "en" else (lambda k: re.sub(r"^(\d{4})-Q(\d)$", r"T\2 \1", k))
    val = (lambda v: f"{v:.2f}") if lang == "en" else (lambda v: f"{v:.2f}".replace(".", ","))
    rows = "".join(f"<tr><th scope=\"row\">{lab(k)}</th><td>{val(series[k])}</td></tr>" for k in keys)
    return (f'<div class="table-scroll"><table class="cal-table"><caption>{esc(u["latest"])} ({esc(u["asof"].lower() if lang == "fr" else u["asof"].lower())} {fdate(CHECKED, lang)})</caption>'
            f'<thead><tr><th scope="col">{esc(u["q"])}</th><th scope="col">{u["v"]}</th></tr></thead><tbody>{rows}</tbody></table></div>')

# ------------------------------------------------------------------ the calendar
SRC = {
    "newlease": ("Service-Public: new lease models from 1 October 2026", "Service-Public : les nouveaux modèles de bail au 1er octobre 2026", "https://www.service-public.gouv.fr/particuliers/actualites/A19067"),
    "tf": ("Service-Public: property tax 2026, deadline to pay", "Service-Public : taxe foncière 2026, date limite de paiement", "https://www.service-public.gouv.fr/particuliers/actualites/A15144"),
    "cap": ("ANIL: the rent-cap trial", "ANIL : l'expérimentation de l'encadrement des loyers", "https://www.anil.org/aj-experimentation-encadrement-niveau-loyers-zones-tendues/"),
    "cfe": ("Service-Public: business property tax (CFE)", "Service-Public : cotisation foncière des entreprises (CFE)", "https://entreprendre.service-public.gouv.fr/vosdroits/F23547"),
    "vac": ("Service-Public: one vacancy tax from 2027 (loi 2026-103, art. 108)", "Service-Public : une taxe unique sur la vacance dès 2027 (loi 2026-103, art. 108)", "https://www.service-public.gouv.fr/particuliers/actualites/A18896"),
    "irl": ("INSEE: IRL, series 001515333", "Insee : IRL, série 001515333", "https://www.insee.fr/fr/statistiques/serie/001515333"),
    "ir": ("Service-Public: income tax return", "Service-Public : déclaration de revenus", "https://www.service-public.gouv.fr/particuliers/vosdroits/F359"),
    "relet": ("Service-Public: rent increases capped until 31 July 2027", "Service-Public : plafonnement des hausses prolongé jusqu'au 31 juillet 2027", "https://www.service-public.gouv.fr/particuliers/actualites/A17566"),
    "rev": ("Service-Public: rent revision during a lease", "Service-Public : révision du loyer en cours de bail", "https://www.service-public.gouv.fr/particuliers/vosdroits/F1311"),
    "dep": ("Service-Public: security deposit", "Service-Public : dépôt de garantie", "https://www.service-public.gouv.fr/particuliers/vosdroits/F31269"),
    "occ": ("Service-Public: property occupancy declaration 2026", "Service-Public : déclaration d'occupation des biens 2026", "https://www.service-public.gouv.fr/particuliers/actualites/A17346"),
}
# kind: fixed (a date set by law or by the tax office) | expected (INSEE's usual timing) | month (only the month is known) | yearly (no fixed date)
CAL = [
    dict(k="newlease", iso="2026-10-01", kind="inforce",
         when=("From 1 October 2026", "À partir du 1er octobre 2026"),
         title=("New model leases apply", "Les nouveaux modèles de bail s'appliquent"),
         what=("Leases signed or renewed from this date use the new model set by décret 2026-596 of 6 July 2026. It covers empty and furnished lets and single-lease flatshares, not mobility leases or holiday lets.",
               "Les baux conclus ou renouvelés à partir de cette date suivent le nouveau modèle fixé par le décret 2026-596 du 6 juillet 2026. Il couvre les locations vides, meublées et les colocations à bail unique, pas les baux mobilité ni les locations saisonnières."),
         who=("Anyone signing or renewing a lease", "Toute personne qui signe ou renouvelle un bail")),
    dict(k="tf", iso="2026-10-20", kind="fixed",
         when=("20 October 2026", "20 octobre 2026"),
         title=("Property tax (taxe foncière): last day to pay online", "Taxe foncière : dernier jour pour payer en ligne"),
         what=("Online payment is due by midnight on 20 October 2026; other payment methods by 15 October. Your own notice shows your date and amount.",
               "Le paiement en ligne est dû avant minuit le 20 octobre 2026 ; les autres modes de paiement avant le 15 octobre. Votre avis indique votre date et votre montant."),
         who=("Owners", "Les propriétaires")),
    dict(k="cap", iso="2026-11-25", kind="fixed",
         when=("25 November 2026 (24 on one official page)", "25 novembre 2026 (24 sur une page officielle)"),
         title=("Rent-cap trial due to end unless Parliament extends it", "Fin prévue de l'expérimentation de l'encadrement des loyers, sauf prolongation"),
         what=("ANIL and the Assemblée nationale bill no. 2039 give 25 November; one Service-Public page says 24. The legal text must settle it. Until then the cap still applies where it applies. See our post for where things stand.",
               "L'ANIL et la proposition de loi n° 2039 de l'Assemblée nationale indiquent le 25 novembre ; une page de Service-Public indique le 24. Le texte de loi doit trancher. D'ici là, l'encadrement s'applique là où il s'applique. Voir notre article pour le point sur le dossier."),
         who=("Landlords in the nine territories", "Les bailleurs des neuf territoires"), post="blog-rent-caps-trial-ending"),
    dict(k="cfe", iso="2026-12-15", kind="fixed",
         when=("15 December 2026", "15 décembre 2026"),
         title=("Business property tax (CFE): balance due", "CFE : solde à payer"),
         what=("In general the balance is due by 15 December inclusive, or the next working day if that is a weekend or holiday. Check whether you owe it: some furnished landlords are exempt.",
               "En général, le solde est dû au plus tard le 15 décembre inclus, ou le premier jour ouvrable suivant si c'est un week-end ou un jour férié. Vérifiez si vous la devez : certains loueurs en meublé en sont exonérés."),
         who=("Landlords who let furnished", "Les loueurs en meublé")),
    dict(k="vac", iso="2027-01-01", kind="fixed",
         when=("1 January 2027", "1er janvier 2027"),
         title=("Vacancy tax: a single tax starts with the 2027 tax year", "Taxe sur la vacance : une taxe unique dès l'imposition 2027"),
         what=("A home counts as vacant if it is empty on 1 January. One tax replaces the two old ones: one year of vacancy in high-demand communes (17%, then 34%), two years elsewhere if the council has introduced it. Years of vacancy before 2027 count.",
               "Un logement est vacant s'il est vide au 1er janvier. Une seule taxe remplace les deux anciennes : un an de vacance dans les communes en forte demande (17 %, puis 34 %), deux ans ailleurs si la commune l'a instituée. Les années de vacance avant 2027 comptent."),
         who=("Owners of an empty home", "Les propriétaires d'un logement vide")),
    dict(k="irl", iso="2027-01-15", kind="expected",
         when=("Around mid-January 2027", "Vers la mi-janvier 2027"),
         title=("IRL for Q4 2026 expected", "IRL du T4 2026 attendu"),
         what=("INSEE publishes each quarter's IRL around the middle of the following month (the Q4 2025 figure came out on 16 January 2026). Leases that name Q4 as their reference quarter can then be revised.",
               "L'Insee publie l'IRL de chaque trimestre vers la mi-mois suivant (celui du T4 2025 est paru le 16 janvier 2026). Les baux dont le trimestre de référence est le T4 peuvent alors être révisés."),
         who=("Landlords revising rent", "Les bailleurs qui révisent le loyer"), tool="irl"),
    dict(k="ir", iso=None, kind="month",
         when=("April 2027", "Avril 2027"),
         title=("Online income tax return opens", "Ouverture de la déclaration de revenus en ligne"),
         what=("The 2027 return, for income earned in 2026, opens in April 2027. The tax office publishes each département's deadline in the spring.",
               "La déclaration 2027, pour les revenus de 2026, ouvre en avril 2027. L'administration fiscale publie la date limite de chaque département au printemps."),
         who=("Everyone with rental income", "Tous les bailleurs percevant des loyers")),
    dict(k="irl", iso="2027-04-15", kind="expected",
         when=("Around mid-April 2027", "Vers la mi-avril 2027"),
         title=("IRL for Q1 2027 expected", "IRL du T1 2027 attendu"),
         what=("The Q1 2026 figure was published on 16 April 2026.", "L'IRL du T1 2026 a été publié le 16 avril 2026."),
         who=("Landlords revising rent", "Les bailleurs qui révisent le loyer"), tool="irl"),
    dict(k="irl", iso="2027-07-15", kind="expected",
         when=("Around mid-July 2027", "Vers la mi-juillet 2027"),
         title=("IRL for Q2 2027 expected", "IRL du T2 2027 attendu"),
         what=("The Q2 2026 figure was published on 12 July 2026.", "L'IRL du T2 2026 a été publié le 12 juillet 2026."),
         who=("Landlords revising rent", "Les bailleurs qui révisent le loyer"), tool="irl"),
    dict(k="relet", iso="2027-07-31", kind="fixed",
         when=("31 July 2027", "31 juillet 2027"),
         title=("Cap on rent increases at relet or renewal: due to end unless renewed", "Plafonnement des hausses à la relocation ou au renouvellement : fin prévue sauf reconduction"),
         what=("A decree of 20 July 2026 extends to 31 July 2027 the cap on rent increases when a home is relet or a lease renewed in high-demand (zone tendue) communes.",
               "Un décret du 20 juillet 2026 prolonge jusqu'au 31 juillet 2027 le plafonnement des hausses de loyer lors d'une relocation ou d'un renouvellement de bail dans les communes en zone tendue."),
         who=("Landlords in high-demand communes", "Les bailleurs en zone tendue")),
    dict(k="rev", iso=None, kind="yearly",
         when=("Every lease anniversary", "À chaque anniversaire du bail"),
         title=("Yearly rent revision", "Révision annuelle du loyer"),
         what=("If the lease has an indexation clause you have one year from the revision date to ask. The increase counts only from your request, and it is lost for that year if you do not ask. Not allowed for a home rated F or G.",
               "Si le bail contient une clause d'indexation, vous avez un an à partir de la date de révision pour la demander. La hausse ne compte qu'à partir de votre demande, et elle est perdue pour l'année si vous ne la demandez pas. Impossible pour un logement classé F ou G."),
         who=("Landlords with an indexation clause", "Les bailleurs dont le bail a une clause d'indexation"), tool="irl"),
    dict(k="dep", iso=None, kind="yearly",
         when=("After the tenant leaves", "Après le départ du locataire"),
         title=("Return the security deposit", "Rendre le dépôt de garantie"),
         what=("One month after the keys are handed back if the exit inventory matches the entry inventory, two months if it does not. Each month started late adds 10% of the monthly rent, excluding charges.",
               "Un mois après la remise des clés si l'état des lieux de sortie est conforme à celui d'entrée, deux mois sinon. Chaque mois de retard commencé ajoute 10 % du loyer mensuel hors charges."),
         who=("Every landlord at the end of a lease", "Tout bailleur à la fin d'un bail"), tool="deposit"),
    dict(k="occ", iso=None, kind="yearly",
         when=("When occupancy changes", "Quand l'occupation change"),
         title=("Property occupancy declaration", "Déclaration d'occupation des biens"),
         what=("Tell the tax office on impots.gouv.fr (\"Gérer mes biens immobiliers\") whether each home is lived in, let or empty. In 2026 the deadline was 30 June. Check the date each spring.",
               "Indiquez à l'administration fiscale sur impots.gouv.fr (« Gérer mes biens immobiliers ») si chaque logement est occupé, loué ou vide. En 2026 la date limite était le 30 juin. Vérifiez la date chaque printemps."),
         who=("Owners", "Les propriétaires")),
]
KIND = {"en": {"inforce": "In force", "fixed": "Fixed date", "expected": "Expected", "month": "Month only", "yearly": "Recurring"},
        "fr": {"inforce": "En vigueur", "fixed": "Date fixe", "expected": "Attendu", "month": "Mois seul", "yearly": "Récurrent"}}
CALUI = {"en": dict(who="Who it concerns", src="Source", checked="Checked", tool="Calculate it", read="Read the post"),
         "fr": dict(who="Qui est concerné", src="Source", checked="Vérifié le", tool="Le calculer", read="Lire l'article")}
TOOL_PAGE = {"irl": {"en": "irl-calculator.html", "fr": "calculateur-irl.html"}, "deposit": {"en": "deposit-calculator.html", "fr": "calculateur-depot-garantie.html"}}
def post_url(slug, lang): return f"{slug}.html" if lang == "en" else f"{slug}-fr.html"

def calendar_html(lang):
    i = 0 if lang == "en" else 1; u = CALUI[lang]; items = []
    for n, e in enumerate(CAL):
        label, label_fr, url = SRC[e["k"]]
        src = (label, label_fr)[i]
        links = f'<a href="{esc(url)}" target="_blank" rel="noopener">{esc(src)}</a>'
        if e.get("tool"): links += f' · <a href="{TOOL_PAGE[e["tool"]][lang]}">{u["tool"]}</a>'
        if e.get("post"): links += f' · <a href="{post_url("blog-rent-caps-trial-ending", lang)}">{u["read"]}</a>'
        when = e["when"][i]
        items.append(f'''<li class="cal-item cal-{e["kind"]}"><div class="cal-when"><span class="cal-date">{esc(when)}</span> <span class="log-tag">{KIND[lang][e["kind"]]}</span></div>
<div class="cal-body"><h2>{esc(e["title"][i])}</h2><p>{esc(e["what"][i])}</p>
<p class="form-note"><strong>{u["who"]}{" :" if lang == "fr" else ":"}</strong> {esc(e["who"][i])}<br>{u["src"]}{" :" if lang == "fr" else ":"} {links} · {u["checked"]} {fdate(CHECKED, lang)}</p></div></li>''')
    return '<ol class="cal-list">\n' + "\n".join(items) + "\n</ol>"

# ------------------------------------------------------------------ the calendar file (.ics)
def _fold(line):
    """RFC 5545: lines are at most 75 bytes; a continuation line starts with one space. Never split a character."""
    out, cur, size, limit = [], "", 0, 75
    for ch in line:
        n = len(ch.encode("utf-8"))
        if size + n > limit:
            out.append(cur); cur, size, limit = " ", 1, 75
        cur += ch; size += n
    out.append(cur); return out
def _text(s): return s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")
def ics_file(lang):
    i = 0 if lang == "en" else 1
    name = {"en": "Domegarde: landlord's calendar, France", "fr": "Domegarde : calendrier du bailleur, France"}[lang]
    L = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Domegarde//Landlord calendar//" + lang.upper(), "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
         "X-WR-CALNAME:" + _text(name), "X-WR-TIMEZONE:Europe/Paris"]
    for n, e in enumerate(CAL):
        if not e["iso"] or e["kind"] == "inforce": continue
        d = e["iso"].replace("-", ""); end = (datetime.date.fromisoformat(e["iso"]) + datetime.timedelta(days=1)).strftime("%Y%m%d")
        title = e["title"][i] + (" (" + KIND[lang]["expected"].lower() + ")" if e["kind"] == "expected" else "")
        desc = f'{e["when"][i]}. {e["what"][i]} {CALUI[lang]["src"]}: {SRC[e["k"]][2]} ({CALUI[lang]["checked"]} {fdate(CHECKED, lang)}).'
        L += ["BEGIN:VEVENT", f"UID:domegarde-calendar-{lang}-{n}-{e['iso']}@domegarde.com", "DTSTAMP:20261016T120000Z",
              f"DTSTART;VALUE=DATE:{d}", f"DTEND;VALUE=DATE:{end}", "SUMMARY:" + _text("Domegarde: " + title if lang == "en" else "Domegarde : " + title),
              "DESCRIPTION:" + _text(desc), "TRANSP:TRANSPARENT",
              "BEGIN:VALARM", "ACTION:DISPLAY", "DESCRIPTION:" + _text(title), "TRIGGER:-P7D", "END:VALARM", "END:VEVENT"]
    L.append("END:VCALENDAR")
    folded = []
    for line in L: folded += _fold(line)
    return "\r\n".join(folded) + "\r\n"
ICS_NAME = {"en": "domegarde-landlord-calendar.ics", "fr": "domegarde-calendrier-bailleur.ics"}

def ics_links(lang):
    t = {"en": ("Add these dates to your calendar", "Downloads a calendar file (.ics) for Apple Calendar, Google Calendar and Outlook. It holds the dated items above, each with a reminder a week before. It is a file on your own device: nothing is subscribed to and nothing is sent to us. Expected IRL dates are marked as expected."),
         "fr": ("Ajouter ces dates à votre agenda", "Télécharge un fichier d'agenda (.ics) pour Apple Calendar, Google Agenda et Outlook. Il contient les échéances datées ci-dessus, chacune avec un rappel une semaine avant. C'est un fichier sur votre appareil : aucun abonnement, rien ne nous est envoyé. Les dates attendues de l'IRL sont signalées comme telles.")}[lang]
    return f'<div class="note-box tool-ics"><h2>{esc(t[0])}</h2><p>{esc(t[1])}</p><p><a class="btn btn-primary" href="/{ICS_NAME[lang]}" download>{esc(t[0])} (.ics)</a></p></div>'

# ------------------------------------------------------------------ the hub
def tool_list(lang):
    items = {"en": [("irl-calculator.html", "Rent revision (IRL) calculator", "Work out your new rent from the INSEE index, with the formula shown and your deadline to claim it."),
                    ("deposit-calculator.html", "Security deposit calculator", "When the deposit must be returned and what a late return costs, from the day the keys were handed back."),
                    ("landlord-calendar.html", "Landlord's calendar", "The dates that matter to a French landlord over the next year, each with its source, and a file for your own calendar.")],
             "fr": [("calculateur-irl.html", "Calculateur de révision du loyer (IRL)", "Calculez votre nouveau loyer avec l'indice de l'Insee, avec la formule affichée et votre date limite pour le demander."),
                    ("calculateur-depot-garantie.html", "Calculateur du dépôt de garantie", "Quand le dépôt doit être rendu et ce que coûte un retard, à partir du jour de la remise des clés."),
                    ("calendrier-bailleur.html", "Calendrier du bailleur", "Les dates qui comptent pour un bailleur en France sur l'année à venir, chacune avec sa source, et un fichier pour votre propre agenda.")]}[lang]
    cta = {"en": "Open the tool", "fr": "Ouvrir l'outil"}[lang]
    return '<div class="tool-grid">' + "".join(f'<a class="tool-tile" href="{f}"><h2>{esc(t)}</h2><p>{esc(d)}</p><span class="tool-open">{cta} →</span></a>' for f, t, d in items) + "</div>"

def fill(body, key, lang):
    reps = {"{{irl-form}}": irl_form, "{{deposit-form}}": deposit_form, "{{irl-table}}": irl_table, "{{calendar}}": calendar_html, "{{ics-links}}": ics_links, "{{tool-list}}": tool_list}
    for token, fn in reps.items():
        body = body.replace(f"<p>{token}</p>", fn(lang))
    assert "{{" not in body, "an unreplaced {{placeholder}} is left in the page"
    return body
