"""
Generator for the Fat Films SEO landing pages.

Produces a standalone static HTML page for every film in /public/films/<slug>.html,
plus four hub pages (films index, about, news, suggest) at /public/<page>.html, and
rewrites /public/sitemap.xml so every page is discoverable by search engines.

Each page is fully self-contained: a single <style> block, a single <script>
block where dynamic behaviour is needed (suggest page), no dependencies on the
main SPA's JavaScript. Run me whenever the film catalogue, descriptions, or
casts change.

Usage:
    python build_seo_pages.py
"""
from __future__ import annotations

from pathlib import Path
from html import escape

ROOT = Path(__file__).resolve().parent
PUBLIC = ROOT / "public"
FILMS_DIR = PUBLIC / "films"
FILMS_DIR.mkdir(parents=True, exist_ok=True)

# -------------------------------------------------------------------------
# Source-of-truth catalogue. `card` and `url_slug` (when present) account
# for filename casing on disk and the user's preferred SEO URL slug; the
# `slug` field is the canonical key used by the main SPA's BY_SLUG map
# (and thus by the /?play=<slug> deep-link).
# -------------------------------------------------------------------------
FILMS = [
    {
        "slug": "american-chud", "title": "American Chud", "original": "American Psycho",
        "card": "american_chud.jpg",
        "title_tag": "American Chud - Fat Films | American Psycho AI Parody",
        "meta_desc": "Fat Films parody of American Psycho. Patrick Ateman is a wealthy Wall Street investment banker with an impeccable morning skincare routine and an insatiable appetite.",
        "desc": "Patrick Ateman is a wealthy Wall Street investment banker with an impeccable morning skincare routine and an insatiable appetite. By day he obsesses over business cards and restaurant reservations. By night, things get a lot messier.",
        "cast": [("Christian Whale","Christian Bale"),("Willem Dafood","Willem Dafoe"),("Jared Lardo","Jared Leto"),("Reese Withoutaspoon","Reese Witherspoon"),("Chloe Sevign-eat","Chloe Sevigny")],
    },
    {
        "slug": "baking-bad", "title": "Baking Bad", "original": "Breaking Bad",
        "card": "baking_bad.jpg",
        "title_tag": "Baking Bad - Fat Films | Breaking Bad AI Parody",
        "meta_desc": "Fat Films parody of Breaking Bad. A high school chemistry teacher gets a devastating diagnosis and decides to use his skills to cook up something far more profitable than school dinners.",
        "desc": "A high school chemistry teacher gets a devastating diagnosis and decides to use his skills to cook up something far more profitable than school dinners. Along with his former student, he builds a snack empire that spirals dangerously out of control.",
        "cast": [("Fryan Cranston","Bryan Cranston"),("Aaron Pork","Aaron Paul"),("Anna Bunn","Anna Gunn"),("Dean Nourish","Dean Norris"),("Bigsy Brandt","Betsy Brandt")],
    },
    {
        "slug": "bigger-things", "title": "Bigger Things", "original": "Stranger Things",
        "card": "Bigger_Things.jpg",
        "title_tag": "Bigger Things - Fat Films | Stranger Things AI Parody",
        "meta_desc": "Fat Films parody of Stranger Things. When a chunky kid vanishes from the small town of Hawkins, his friends discover something monstrous lurking in the Upside Down.",
        "desc": "When a chunky kid vanishes from the small town of Hawkins, his friends discover something monstrous lurking in a parallel dimension called the Upside Down. Turns out the real stranger thing is how much these kids can eat during a crisis.",
        "cast": [("Millie Gobby Brown","Millie Bobby Brown"),("Sharkfin Wolfhard","Finn Wolfhard"),("Winona Wider","Winona Ryder"),("Gaten Mozzarella","Gaten Matarazzo"),("Caleb McLovin","Caleb McLaughlin")],
    },
    {
        "slug": "bulk-fiction", "title": "Bulk Fiction", "original": "Pulp Fiction",
        "card": "Bulk_Fiction.jpg",
        "title_tag": "Bulk Fiction - Fat Films | Pulp Fiction AI Parody",
        "meta_desc": "Fat Films parody of Pulp Fiction. The lives of two heavyweight hitmen, a mob boss's wife with a taste for milkshakes, and a boxer who refuses to go down.",
        "desc": "The lives of two heavyweight hitmen, a mob boss's wife with a taste for milkshakes, and a boxer who refuses to go down intertwine across Los Angeles. Non-linear storytelling has never been this filling.",
        "cast": [("John Truffolta","John Travolta"),("Samuel L. Snackson","Samuel L. Jackson"),("Uma Thickman","Uma Thurman"),("Bruce Widest","Bruce Willis"),("Tim Broth","Tim Roth")],
    },
    {
        "slug": "chewlander", "title": "Chewlander", "original": "Zoolander",
        "card": "Chewlander.jpg",
        "title_tag": "Chewlander - Fat Films | Zoolander AI Parody",
        "meta_desc": "Fat Films parody of Zoolander. Derek Chewlander is the world's most famous male model, known for his signature look Blue Meal.",
        "desc": "Derek Chewlander is the world's most famous male model, known for his signature look Blue Meal. When a sinister fashion mogul tries to use him as a weapon, Derek must team up with rival model Hamsel to save the day and look absolutely stuffed doing it.",
        "cast": [("Ben Filler","Ben Stiller"),("Owen Wideson","Owen Wilson"),("Whale Ferrell","Will Ferrell"),("Crusty Taylor","Christine Taylor"),("Millan KG Jovovich","Milla Jovovich")],
    },
    {
        "slug": "chiplash", "title": "Chiplash", "original": "Whiplash",
        "card": "Chiplash.jpg",
        "title_tag": "Chiplash - Fat Films | Whiplash AI Parody",
        "meta_desc": "Fat Films parody of Whiplash. A young jazz drummer enrols at a prestigious music conservatory, only to face the tyrannical instruction of Terence Flesher.",
        "desc": "A young jazz drummer enrols at one of the most prestigious music conservatories in the country, only to find himself under the tyrannical instruction of Terence Flesher, a conductor who pushes his students well past their breaking point. Not quite my tempo, not quite my portion size.",
        "cast": [("Miles Sweller","Miles Teller"),("K.G. Simmons","J.K. Simmons"),("Paul Raisin","Paul Reiser"),("Beluga Beignet","Melissa Benoist"),("Austin Stowswell","Austin Stowell")],
    },
    {
        "slug": "donnie-lardo", "title": "Donnie Lardo", "original": "Donnie Darko",
        "card": "donnie_lardo.jpg",
        "title_tag": "Donnie Lardo - Fat Films | Donnie Darko AI Parody",
        "meta_desc": "Fat Films parody of Donnie Darko. A troubled teenager starts sleepwalking and having visions of a giant terrifying rabbit who tells him the world is about to end.",
        "desc": "A troubled teenager starts sleepwalking and having visions of a giant terrifying rabbit who tells him the world is about to end. Between existential dread and raiding the fridge at 3am, Donnie has a lot on his plate. Literally.",
        "cast": [("Bake Gyllenhaal","Jake Gyllenhaal"),("Jena Baloney","Jena Malone"),("Drew Berrymore","Drew Barrymore"),("Fatrick Swayze","Patrick Swayze"),("Mary McDonalds","Mary McDonnell")],
    },
    {
        "slug": "fat-club", "title": "Fat Club", "original": "Fight Club",
        "card": "fat_club.jpg",
        "title_tag": "Fat Club - Fat Films | Fight Club AI Parody",
        "meta_desc": "Fat Films parody of Fight Club. An insomniac office worker and a mysterious soap salesman form an underground club with one simple rule.",
        "desc": "An insomniac office worker and a mysterious soap salesman form an underground club with one simple rule: nobody talks about Fat Club. What starts as bare-knuckle brawling quickly inflates into something much, much bigger.",
        "cast": [("Brad Pitt-a","Brad Pitt"),("Breadward Norton","Edward Norton"),("Helena Bonham Fatter","Helena Bonham Carter"),("Meat Loaf","Meat Loaf"),("Jared Lardo","Jared Leto")],
    },
    {
        "slug": "fat-runner", "title": "Fat Runner", "original": "Blade Runner 2049",
        "card": "fat_runner.jpg",
        "title_tag": "Fat Runner - Fat Films | Blade Runner 2049 AI Parody",
        "meta_desc": "Fat Films parody of Blade Runner 2049. Officer KD6-3.7 is a blade runner tasked with hunting down rogue replicants in a dystopian 2049.",
        "desc": "Officer KD6-3.7 is a blade runner tasked with hunting down rogue replicants in a dystopian 2049. When he uncovers a long-buried secret, he must find former blade runner Rick Deckard, who has been in hiding and apparently eating very well.",
        "cast": [("Ryan Gobbling","Ryan Gosling"),("Harrison Lard","Harrison Ford"),("Ana de Armass","Ana de Armas"),("Jared Lardo","Jared Leto"),("Robin Wide","Robin Wright")],
    },
    {
        "slug": "fatsi-driver", "title": "Fatsi Driver", "original": "Taxi Driver",
        "card": "fatsy_driver.jpg",
        "title_tag": "Fatsi Driver - Fat Films | Taxi Driver AI Parody",
        "meta_desc": "Fat Films parody of Taxi Driver. Travis Bickling is a lonely cab driver navigating the greasy streets of 1970s New York City.",
        "desc": "Travis Bickling is a lonely, sleep-deprived cab driver navigating the greasy streets of 1970s New York City. Disgusted by the filth and corruption he sees through his windshield, he embarks on a one-man mission to clean up the city, fuelled entirely by diner food.",
        "cast": [("Robert De Nobu","Robert De Niro"),("Jodie Fodder","Jodie Foster"),("Cybill Shephards Pie","Cybill Shepherd"),("Harvey Pie-tel","Harvey Keitel"),("Albert Cookies","Albert Brooks")],
    },
    {
        "slug": "heavy-potter", "title": "Heavy Potter", "original": "Harry Potter",
        "card": "Heavy_Potter.jpg",
        "title_tag": "Heavy Potter - Fat Films | Harry Potter AI Parody",
        "meta_desc": "Fat Films parody of Harry Potter. An orphan living under the stairs discovers he's actually a wizard and gets whisked away to Hogwarts.",
        "desc": "An orphan living under the stairs discovers he's actually a wizard and gets whisked away to Hogwarts School of Witchcraft and Wizardry. Between battling the dark lord and demolishing the Great Hall buffet, Heavy's plate is always full.",
        "cast": [("Daniel Fatcliffe","Daniel Radcliffe"),("Emma Whatson-the-menu","Emma Watson"),("Rupert Grub","Rupert Grint"),("Alan Snackman","Alan Rickman"),("Mouth Fiennes","Ralph Fiennes")],
    },
    {
        "slug": "interbelly", "title": "Interbelly", "original": "Interstellar",
        "card": "interbelly.jpg",
        "title_tag": "Interbelly - Fat Films | Interstellar AI Parody",
        "meta_desc": "Fat Films parody of Interstellar. In a dying future where crops have failed, a former NASA pilot leads a crew through a wormhole in search of a new home.",
        "desc": "In a dying future where crops have failed and humanity faces starvation, a former NASA pilot leads a crew through a wormhole in search of a new home. The mission: find a planet with enough food to feed everyone. Time is relative but hunger is constant.",
        "cast": [("Fatthew McConaughey","Matthew McConaughey"),("Anne Hatha-weigh","Anne Hathaway"),("Jessica Chas-stain","Jessica Chastain"),("Michael Grain","Michael Caine"),("Fatt Damon","Matt Damon")],
    },
    {
        "slug": "squid-gain", "title": "Squid Gain", "original": "Squid Game",
        "card": "squid_gain.jpg",
        "title_tag": "Squid Gain - Fat Films | Squid Game AI Parody",
        "meta_desc": "Fat Films parody of Squid Game. Hundreds of cash-strapped contestants compete in deadly childhood games for a massive cash prize.",
        "desc": "Hundreds of cash-strapped contestants accept a mysterious invitation to compete in a series of deadly childhood games for a massive cash prize. The stakes are enormous. So are the players.",
        "cast": [("Pea Jung-Jae","Lee Jung-jae"),("Park Hae-soup","Park Hae-soo"),("Wi Ham-joon","Wi Ha-joon"),("Jung Ho-yum","Jung Ho-yeon"),("Gong Food","Gong Yoo")],
    },
    {
        "slug": "the-bigs", "title": "The Bigs", "original": "The Boys",
        "card": "the_bigs.jpg",
        "title_tag": "The Bigs - Fat Films | The Boys AI Parody",
        "meta_desc": "Fat Films parody of The Boys. A ragtag group of vigilantes take on corrupt superheroes who abuse their powers for fame and profit.",
        "desc": "A ragtag group of vigilantes take on corrupt superheroes who abuse their powers for fame and profit. Leading the charge is Billy Butcher, a man with a grudge, a plan, and absolutely zero interest in portion control.",
        "cast": [("Karl Bourbon","Karl Urban"),("Pack Quaid","Jack Quaid"),("Whamtony Starr","Antony Starr"),("Erin Moritarty","Erin Moriarty"),("Dominique McElligut","Dominique McElligott")],
    },
    {
        "slug": "the-fatrix", "title": "The Fatrix", "original": "The Matrix",
        "card": "The_Fatrix.jpg",
        "title_tag": "The Fatrix - Fat Films | The Matrix AI Parody",
        "meta_desc": "Fat Films parody of The Matrix. A computer hacker discovers that reality is a simulated world designed to keep humanity docile and well-fed.",
        "desc": "A computer hacker discovers that reality as he knows it is actually a simulated world designed to keep humanity docile and well-fed. When offered the choice between a red pill and a blue pill, Neo asks if there is a third option with gravy.",
        "cast": [("Keanu Feeds","Keanu Reeves"),("Laurence Fishbone","Laurence Fishburne"),("Carrie-Pan Moss","Carrie-Anne Moss"),("Huge Weaving","Hugo Weaving"),("Joe Panini-ano","Joe Pantoliano")],
    },
    {
        # User's spec URL is /films/the-weight-of-wallstreet.html, but the SPA slug
        # is "weight-of-wallstreet" — pin play_slug separately so /?play= still works.
        "slug": "weight-of-wallstreet", "url_slug": "the-weight-of-wallstreet",
        "title": "The Weight of Wallstreet", "original": "The Wolf of Wall Street",
        "card": "The_Weight_of_Wallstreet.jpg",
        "title_tag": "The Weight of Wallstreet - Fat Films | Wolf of Wall Street AI Parody",
        "meta_desc": "Fat Films parody of The Wolf of Wall Street. The true story of Jordan Belfry, a stockbroker who built a massive fortune through fraud, excess, and appetite.",
        "desc": "Based on the true story of Jordan Belfry, a stockbroker who built a massive fortune through fraud, excess, and an appetite for the finer things in life. The money was obscene, the parties were legendary, and the lunch bills were astronomical.",
        "cast": [("Leonardo DiCarpaccio","Leonardo DiCaprio"),("Jonah Fill","Jonah Hill"),("Margot Gobbie","Margot Robbie"),("Fatthew McConaughey","Matthew McConaughey"),("Piele Chandler","Kyle Chandler")],
    },
    {
        "slug": "whoppenheimer", "title": "Whoppenheimer", "original": "Oppenheimer",
        "card": "Whoppenheimer.jpg",
        "title_tag": "Whoppenheimer - Fat Films | Oppenheimer AI Parody",
        "meta_desc": "Fat Films parody of Oppenheimer. The story of J. Robert Whoppenheimer, the physicist who led the development of the world's first weapon of mass consumption.",
        "desc": "The story of J. Robert Whoppenheimer, the physicist who led the development of the world's first weapon of mass consumption. As the mushroom cloud rises, so does his waistline. Now he must face the consequences of creating something the world can never un-eat.",
        "cast": [("Celery Murphy","Cillian Murphy"),("Robert Brownie Jr.","Robert Downey Jr."),("Emily Bluntcake","Emily Blunt"),("Fatt Damon","Matt Damon"),("Florence Pudding","Florence Pugh")],
    },
    {
        "slug": "jurassic-pork", "title": "Jurassic Pork", "original": "Jurassic Park",
        "card": "Jurassic_Pork.jpg",
        "title_tag": "Jurassic Pork - Fat Films | Jurassic Park AI Parody",
        "meta_desc": "Fat Films parody of Jurassic Park. A well-fed billionaire invites scientists to his theme park where he's cloned dinosaurs using ancient DNA preserved in deep-fried amber.",
        "desc": "A well-fed billionaire invites a group of scientists to his extraordinary new theme park on a remote island, where he's managed to clone dinosaurs using ancient DNA preserved in deep-fried amber. But when the security systems fail and the hungry dinos break loose, the visitors quickly learn they're no longer at the top of the food chain. Life finds a way, and so does the appetite.",
        "cast": [("Ham Neill","Sam Neill"),("Larger Dern","Laura Dern"),("Jeff Goldplum","Jeff Goldblum"),("Richlard Attenborough","Richard Attenborough"),("Samuel L. Snackson","Samuel L. Jackson")],
    },
    {
        "slug": "fatman", "title": "Fatman", "original": "Batman",
        "card": "Fatman.jpg",
        "title_tag": "Fatman - Fat Films | Batman AI Parody",
        "meta_desc": "Fat Films parody of Batman. Gotham City is a cesspit of crime, corruption, and questionable takeaway options. When the Fatman emerges from the shadows, criminals learn to fear the night.",
        "desc": "Gotham City is a cesspit of crime, corruption, and questionable takeaway options. When the Fatman emerges from the shadows, criminals learn to fear the night, and every late-night kebab shop learns to fear his appetite. Armed with nothing but a utility belt struggling to hold itself together and a cave full of snacks, Bruce Weighne wages a one-man war on crime between meals. But when a new villain threatens to shut down every restaurant in Gotham, the Fatman must rise to protect the one thing he truly cares about.",
        "cast": [("Globert Pattinson","Robert Pattinson"),("Zoe Kraveitz","Zoe Kravitz"),("Colin Fattell","Colin Farrell"),("Pork Dano","Paul Dano"),("Jeffrey Wide","Jeffrey Wright")],
    },
    {
        "slug": "lord-of-the-onion-rings", "title": "Lord of the Onion Rings", "original": "The Lord of the Rings",
        "card": "Lord_of_the_Onion_Rings.jpg",
        "title_tag": "Lord of the Onion Rings - Fat Films | Lord of the Rings AI Parody",
        "meta_desc": "Fat Films parody of Lord of the Rings. In the land of Middle Girth, a plump young hobbit inherits a powerful ring, deep fried in the fires of Mount Doom.",
        "desc": "In the land of Middle Girth, a plump young hobbit inherits a powerful ring, deep fried in the fires of Mount Doom. Burdened with destroying it, Frodo sets off on an epic, calorie-burning journey with a fellowship of warriors, wizards, and extremely well-fed companions, fuelled by second breakfasts and lembas bread. But the ring whispers promises of unlimited sides and bottomless refills. One ring to rule them all, one ring to find them, one ring to bring them all, and in the deep fat fryer, bind them.",
        "cast": [("Elijah Food","Elijah Wood"),("Ian McJellin","Ian McKellen"),("Biggo Mortensen","Viggo Mortensen"),("Orzo Bloom","Orlando Bloom"),("Sean Fatsin","Sean Astin")],
    },
    {
        "slug": "dextra-large", "title": "Dextra Large", "original": "Dexter",
        "card": "Dextra_Large.jpg",
        "title_tag": "Dextra Large - Fat Films | Dexter AI Parody",
        "meta_desc": "Fat Films parody of Dexter. Dexter Moron is Miami's most beloved forensic analyst by day, and the city's most insatiable snacker by night.",
        "desc": "Dexter Moron is Miami's most beloved forensic analyst by day, and the city's most insatiable snacker by night. While his colleagues chase down suspects, Dexter follows his own Dark Passenger, an uncontrollable urge leading him to every all-you-can-eat restaurant in South Florida. As the portions get larger and the buffet bills pile up, he must keep his monstrous appetite hidden from everyone around him. Some people live for the thrill. Dexter lives for seconds.",
        "cast": [("Michael C. Wall","Michael C. Hall"),("Jennifer Carpeater","Jennifer Carpenter"),("James Remarinated","James Remar"),("Flavoured Zayas","David Zayas"),("Lauren Filet","Lauren Velez")],
    },
    {
        "slug": "superfat", "title": "Superfat", "original": "Superbad",
        "card": "Superfat.jpg",
        "title_tag": "Superfat - Fat Films | Superbad AI Parody",
        "meta_desc": "Fat Films parody of Superbad. Two overweight best friends are about to graduate high school with one mission: get invited to the biggest house party of the year.",
        "desc": "Two overweight, unpopular best friends are about to graduate high school with one mission: get invited to the biggest house party of the year and finally impress the girls they've been drooling over since freshman year. Armed with a fake ID belonging to a 25 year old Hawaiian organ donor named McLovin, the duo embark on a chaotic night of mishaps, misunderstandings, and an unholy amount of gas station snacks. Everything that can go wrong does go wrong, but at least the vending machines still work. One night. Two hungry legends. Zero chance of fitting into their prom suits.",
        "cast": [("Jonah Fill","Jonah Hill"),("Michael Cereal","Michael Cera"),("Christopher Mince-Plasse","Christopher Mintz-Plasse"),("Fill Hader","Bill Hader"),("Seth Hogen","Seth Rogen")],
    },
    {
        "slug": "limitmass", "title": "Limitmass", "original": "Limitless",
        "card": "Limitmass.jpg",
        "title_tag": "Limitmass - Fat Films | Limitless AI Parody",
        "meta_desc": "Fat Films parody of Limitless. Eddie Moron discovers a mysterious pill that unlocks 100% of his brain's appetite.",
        "desc": "Eddie Moron discovers a mysterious pill that unlocks 100% of his brain's appetite. Overnight he goes from a broke, unmotivated writer to a man who can consume information and calories at an inhuman rate. But as his hunger for success grows, so does his waistline. With dangerous side effects kicking in and powerful people wanting the pill for themselves, Eddie learns that there's no such thing as a free lunch. Except there literally is, because he can now afford hundreds of them.",
        "cast": [("Breadly Cooper","Bradley Cooper"),("Blobert De Niro","Robert De Niro"),("Abbie Corndog","Abbie Cornish"),("Andrew Coward","Andrew Howard"),("Anna Fridge","Anna Friel")],
    },
    {
        "slug": "no-country-for-fat-men", "title": "No Country for Fat Men", "original": "No Country for Old Men",
        "card": "no_country_for_fat_men.jpg",
        "title_tag": "No Country for Fat Men - Fat Films | No Country for Old Men AI Parody",
        "meta_desc": "Fat Films parody of No Country for Old Men. A hunter stumbles upon a suitcase full of cash in the desert and is pursued by a relentless hitman.",
        "desc": "When a hunter stumbles upon a suitcase full of cash in the middle of the desert, he makes the fatal mistake of taking it. Now being pursued by a relentless, unstoppable hitman with the world's most terrifying bowl cut and an even more terrifying appetite, he must run for his life across the dusty plains of West Texas. The only question is whether he'll run out of road or run out of snacks first. What's the most you've ever lost on a coin toss? Probably less than what this man spends on drive-throughs.",
        "cast": [("Javier Lardem","Javier Bardem"),("Josh Brownie","Josh Brolin"),("Tommy Cheese Jones","Tommy Lee Jones"),("Foody Harrelson","Woody Harrelson"),("Kelly McDondalds","Kelly Macdonald")],
    },
    {
        "slug": "the-eating-dead", "title": "The Eating Dead", "original": "The Walking Dead",
        "card": "The_Eating_Dead.jpg",
        "title_tag": "The Eating Dead - Fat Films | The Walking Dead AI Parody",
        "meta_desc": "Fat Films parody of The Walking Dead. The world has ended. The dead have risen. And somehow, they're still hungry.",
        "desc": "The world has ended. The dead have risen. And somehow, they're still hungry. Sheriff Rick Grimes wakes up from a coma to find civilisation in ruins and hordes of the undead roaming the streets looking for their next meal. As he searches for his family, he bands together with a group of survivors who must fight not just the walkers, but their own growing appetites in a world where every tin of beans could be your last. In this world, it's eat or be eaten. Literally.",
        "cast": [("Andrew Lickoln","Andrew Lincoln"),("Norman Feedus","Norman Reedus"),("Steven Yeunomnom","Steven Yeun"),("Lauren Coham","Lauren Cohan"),("Danai Grillria","Danai Gurira")],
    },
    {
        "slug": "the-hungry-games", "title": "The Hungry Games", "original": "The Hunger Games",
        "card": "The_Hungry_Games.jpg",
        "title_tag": "The Hungry Games - Fat Films | The Hunger Games AI Parody",
        "meta_desc": "Fat Films parody of The Hunger Games. In a dystopian future, 24 teenagers compete in a televised fight to the death for a lifetime supply of food.",
        "desc": "In a dystopian future where the rich feast and the poor starve, 24 teenagers are selected each year to compete in The Hungry Games, a televised fight to the death where the last one standing wins a lifetime supply of food for their district. When Katniss Everdeen volunteers to take her sister's place, she enters an arena where survival depends on skill, strategy, and knowing which berries are safe to eat. May the forks be ever in your flavour.",
        "cast": [("Jennifer Lardrence","Jennifer Lawrence"),("Josh Muncherson","Josh Hutcherson"),("Liam Heavsworth","Liam Hemsworth"),("Foody Harrelson","Woody Harrelson"),("Elizabeth Snacks","Elizabeth Banks")],
    },
]


def url_slug(film: dict) -> str:
    """SEO URL slug — usually the same as the SPA slug."""
    return film.get("url_slug", film["slug"])


def play_slug(film: dict) -> str:
    """The slug used in /?play= deep-links (matches the SPA BY_SLUG key)."""
    return film["slug"]


SOCIALS_SVG = {
    "instagram": '<svg viewBox="0 0 24 24"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z"/></svg>',
    "tiktok": '<svg viewBox="0 0 24 24"><path d="M19.59 6.69a4.83 4.83 0 01-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 01-2.88 2.5 2.89 2.89 0 01-2.89-2.89 2.89 2.89 0 012.89-2.89c.28 0 .54.04.79.1v-3.5a6.37 6.37 0 00-.79-.05A6.34 6.34 0 003.15 15.2a6.34 6.34 0 0010.86 4.48v-7.15a8.16 8.16 0 005.58 2.18v-3.44a4.85 4.85 0 01-1.99-.58z"/></svg>',
    "x": '<svg viewBox="0 0 24 24"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>',
}

SEO_BLURB = (
    "Fat Films is a viral AI entertainment project recreating iconic scenes from popular "
    "films and TV shows, reimagining every character as FAT. With millions of views across "
    "TikTok and Instagram, Fat Films has become one of the most popular AI video projects on "
    "the internet. Watch all Fat Films originals, suggest new films, and join the community at "
    "fatfilms.org. Fat Films has a community Solana token, $fatfilms, launched on Pumpfun."
)


SHARED_CSS = """
*, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }
html, body {
  background: #0a0a0a;
  color: #e5e5e5;
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
  min-height: 100vh;
  -webkit-font-smoothing: antialiased;
}
a { color: inherit; text-decoration: none; }
img { display: block; max-width: 100%; }

/* NAV */
.seo-nav {
  position: sticky; top: 0; z-index: 20;
  background: rgba(10,10,10,0.92);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(255,255,255,0.06);
  padding: 14px 32px;
  display: flex; align-items: center; gap: 32px;
  flex-wrap: wrap;
}
.seo-nav .brand {
  font-family: 'Bebas Neue', sans-serif;
  font-size: 1.4rem; letter-spacing: 3px;
  color: #fff;
  text-shadow: 0 0 12px rgba(229,9,20,0.3);
}
.seo-nav .links { display: flex; gap: 24px; margin-left: auto; }
.seo-nav .links a {
  color: #ccc; font-size: 0.92rem; font-weight: 500;
  padding: 4px 0;
  transition: color 0.15s;
}
.seo-nav .links a:hover { color: #fff; }
@media (max-width: 640px) {
  .seo-nav { padding: 10px 16px; gap: 12px; }
  .seo-nav .brand { font-size: 1.15rem; letter-spacing: 2px; }
  .seo-nav .links { gap: 12px; margin-left: 0; width: 100%; justify-content: flex-start; flex-wrap: wrap; }
  .seo-nav .links a { font-size: 0.82rem; }
}

/* FILM HERO */
.hero {
  position: relative;
  min-height: 70vh;
  display: flex; align-items: flex-end;
  padding: 80px 40px;
  background-size: cover; background-position: center;
  background-color: #111;
}
.hero::before {
  content: ''; position: absolute; inset: 0;
  background: linear-gradient(180deg, rgba(10,10,10,0.4) 0%, rgba(10,10,10,0.7) 60%, rgba(10,10,10,1) 100%),
              linear-gradient(90deg, rgba(10,10,10,0.7) 0%, rgba(10,10,10,0.3) 60%, rgba(10,10,10,0) 100%);
  pointer-events: none;
}
.hero-inner { position: relative; z-index: 1; max-width: 800px; }
.hero h1 {
  font-family: 'Bebas Neue', sans-serif;
  font-size: clamp(2.8rem, 7vw, 5.5rem);
  letter-spacing: 5px;
  color: #fff;
  text-shadow: 3px 3px 8px rgba(0,0,0,0.85);
  margin-bottom: 12px;
  line-height: 1;
}
.parody-of {
  font-size: 1.02rem; color: #c8c8c8;
  margin-bottom: 24px;
  text-shadow: 0 1px 4px rgba(0,0,0,0.8);
}
.parody-of strong { color: #fff; font-weight: 700; }
.hero-actions { display: flex; gap: 12px; flex-wrap: wrap; }
.btn-primary {
  background: #e50914; color: #fff;
  padding: 13px 28px; border-radius: 4px;
  font-weight: 700; font-size: 1rem;
  display: inline-flex; align-items: center; gap: 8px;
  border: none; cursor: pointer; font-family: inherit;
  transition: background 0.15s, transform 0.1s;
}
.btn-primary:hover { background: #f6121d; }
.btn-primary:active { transform: scale(0.98); }
.btn-secondary {
  background: rgba(255,255,255,0.12); color: #fff;
  padding: 13px 24px; border-radius: 4px;
  font-weight: 600; font-size: 0.95rem;
  border: 1px solid rgba(255,255,255,0.15);
  backdrop-filter: blur(4px);
  transition: background 0.15s;
  display: inline-flex; align-items: center; gap: 8px;
  cursor: pointer; font-family: inherit;
}
.btn-secondary:hover { background: rgba(255,255,255,0.2); }
@media (max-width: 640px) {
  .hero { padding: 50px 20px; min-height: 60vh; }
  .hero h1 { letter-spacing: 3px; }
}

/* SECTIONS */
.section { padding: 64px 40px; max-width: 1200px; margin: 0 auto; }
.section h2 {
  font-family: 'Bebas Neue', sans-serif;
  font-size: clamp(1.8rem, 3vw, 2.4rem); letter-spacing: 2px;
  color: #fff; margin-bottom: 24px;
}
.synopsis {
  font-size: 1.1rem; line-height: 1.7; color: #cdcdcd;
  max-width: 800px;
}
@media (max-width: 640px) {
  .section { padding: 40px 20px; }
  .synopsis { font-size: 1rem; }
}

/* CAST */
.cast {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
}
.cast-item {
  background: #141414;
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 8px;
  padding: 18px 18px 16px;
  transition: border-color 0.15s;
}
.cast-item:hover { border-color: rgba(255,255,255,0.18); }
.cast-fake {
  font-family: 'Bebas Neue', sans-serif;
  font-size: 1.4rem; letter-spacing: 1.5px;
  color: #fff; line-height: 1.15;
}
.cast-real {
  font-size: 0.8rem; color: #888;
  margin-top: 6px;
}

/* RECS GRID — also used by /films hub */
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 18px;
}
.card {
  background: #141414;
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 8px;
  overflow: hidden;
  transition: transform 0.2s, border-color 0.2s;
  display: block;
}
.card:hover { transform: translateY(-3px); border-color: rgba(255,255,255,0.2); }
.card img {
  width: 100%; aspect-ratio: 16 / 9; object-fit: cover;
  background: #222;
}
.card-body { padding: 14px 16px; }
.card-fake {
  font-family: 'Bebas Neue', sans-serif;
  font-size: 1.25rem; letter-spacing: 1px;
  color: #fff;
}
.card-orig { font-size: 0.8rem; color: #888; margin-top: 3px; }

/* FOOTER */
.seo-footer {
  margin-top: 40px;
  padding: 50px 40px 30px;
  border-top: 1px solid rgba(255,255,255,0.06);
  text-align: center;
}
.socials {
  display: flex; justify-content: center; gap: 32px;
  flex-wrap: wrap; margin-bottom: 28px;
}
.socials a {
  display: inline-flex; align-items: center; gap: 8px;
  color: #bbb; font-size: 0.92rem; font-weight: 600;
  transition: color 0.15s;
}
.socials a:hover { color: #fff; }
.socials svg { width: 20px; height: 20px; fill: currentColor; }
.seo-blurb {
  color: rgba(255,255,255,0.3);
  font-size: 12px; line-height: 1.6;
  max-width: 900px; margin: 0 auto;
  letter-spacing: 0.2px;
}
@media (max-width: 640px) {
  .seo-footer { padding: 36px 20px 20px; }
  .socials { gap: 22px; }
}
"""


def render_head(title_tag: str, meta_desc: str, canonical: str, og_image: str, og_type: str = "website") -> str:
    return f"""<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escape(title_tag)}</title>
<meta name="description" content="{escape(meta_desc)}">
<meta property="og:title" content="{escape(title_tag)}">
<meta property="og:description" content="{escape(meta_desc)}">
<meta property="og:url" content="{escape(canonical)}">
<meta property="og:type" content="{og_type}">
<meta property="og:image" content="{escape(og_image)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{escape(title_tag)}">
<meta name="twitter:description" content="{escape(meta_desc)}">
<meta name="google-site-verification" content="TizUvxnu-crJd_PCyDW-8FBZYRmGv23YCelZvU0YFJ0">
<link rel="canonical" href="{escape(canonical)}">
<link rel="icon" href="/favicon.png" type="image/png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;500;600;700;900&display=swap" rel="stylesheet">
<style>{SHARED_CSS}</style>"""


NAV = """<nav class="seo-nav">
  <a href="https://fatfilms.org" class="brand">FAT FILMS</a>
  <div class="links">
    <a href="/films">Films</a>
    <a href="/suggest">Suggest a Film</a>
    <a href="/about">About</a>
    <a href="/news">News</a>
    <a href="https://fatfilms.org">Watch</a>
  </div>
</nav>"""


FOOTER = f"""<footer class="seo-footer">
  <div class="socials">
    <a href="https://www.instagram.com/fatfilmz_" target="_blank" rel="noopener">
      {SOCIALS_SVG['instagram']}<span>Instagram</span>
    </a>
    <a href="https://www.tiktok.com/@fatfilms_" target="_blank" rel="noopener">
      {SOCIALS_SVG['tiktok']}<span>TikTok</span>
    </a>
    <a href="https://x.com/fatfilmsparody" target="_blank" rel="noopener">
      {SOCIALS_SVG['x']}<span>X / Twitter</span>
    </a>
  </div>
  <p class="seo-blurb">{escape(SEO_BLURB)}</p>
</footer>"""


VERCEL_ANALYTICS = '<script defer src="/_vercel/insights/script.js"></script>'


def pick_recommendations(films: list[dict], index: int, n: int = 4) -> list[dict]:
    """Deterministic round-robin selection of n other films."""
    picks = []
    step = max(1, len(films) // (n + 1))
    cursor = (index + step) % len(films)
    while len(picks) < n and len(picks) < len(films) - 1:
        if cursor != index and films[cursor] not in picks:
            picks.append(films[cursor])
        cursor = (cursor + step) % len(films)
        if cursor == (index + step) % len(films) and picks:
            # Wrapped around — fall back to a sequential walk.
            cursor = (index + 1) % len(films)
            while len(picks) < n and len(picks) < len(films) - 1:
                if cursor != index and films[cursor] not in picks:
                    picks.append(films[cursor])
                cursor = (cursor + 1) % len(films)
            break
    return picks


def render_film_page(film: dict, recs: list[dict]) -> str:
    canonical = f"https://fatfilms.org/films/{url_slug(film)}"
    og_image = f"https://fatfilms.org/titlecards/{film['card']}"
    head = render_head(film["title_tag"], film["meta_desc"], canonical, og_image, og_type="video.movie")

    cast_html = "\n".join(
        f'      <div class="cast-item"><div class="cast-fake">{escape(fake)}</div><div class="cast-real">{escape(real)}</div></div>'
        for fake, real in film["cast"]
    )

    recs_html = "\n".join(
        f'      <a class="card" href="/films/{url_slug(r)}">\n'
        f'        <img src="/titlecards/{r["card"]}" alt="{escape(r["title"])}" loading="lazy">\n'
        f'        <div class="card-body"><div class="card-fake">{escape(r["title"])}</div>'
        f'<div class="card-orig">parody of {escape(r["original"])}</div></div>\n'
        f'      </a>'
        for r in recs
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
{head}
</head>
<body>

{NAV}

<section class="hero" style="background-image: url('/titlecards/{film['card']}');">
  <div class="hero-inner">
    <h1>{escape(film['title'])}</h1>
    <p class="parody-of">A Fat Films parody of <strong>{escape(film['original'])}</strong></p>
    <div class="hero-actions">
      <a class="btn-primary" href="https://fatfilms.org/?play={play_slug(film)}">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
        Watch Now
      </a>
      <a class="btn-secondary" href="/films">Browse All Films</a>
    </div>
  </div>
</section>

<section class="section">
  <h2>Synopsis</h2>
  <p class="synopsis">{escape(film['desc'])}</p>
</section>

<section class="section">
  <h2>Cast</h2>
  <div class="cast">
{cast_html}
  </div>
</section>

<section class="section">
  <h2>You might also like</h2>
  <div class="grid">
{recs_html}
  </div>
</section>

{FOOTER}

{VERCEL_ANALYTICS}

</body>
</html>
"""


def render_films_hub(films: list[dict]) -> str:
    head = render_head(
        "All Films - Fat Films | AI Movie Parodies",
        "Browse all Fat Films AI movie parodies. Watch iconic film scenes recreated with every character made fat using cutting-edge AI.",
        "https://fatfilms.org/films",
        "https://fatfilms.org/titlecards/fat_club.jpg",
    )

    cards = "\n".join(
        f'    <a class="card" href="/films/{url_slug(f)}">\n'
        f'      <img src="/titlecards/{f["card"]}" alt="{escape(f["title"])} - {escape(f["original"])} parody" loading="lazy">\n'
        f'      <div class="card-body"><div class="card-fake">{escape(f["title"])}</div>'
        f'<div class="card-orig">parody of {escape(f["original"])}</div></div>\n'
        f'    </a>'
        for f in films
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
{head}
</head>
<body>

{NAV}

<section class="section" style="padding-top: 50px;">
  <h2 style="font-size: clamp(2.2rem, 4vw, 3.4rem); margin-bottom: 8px;">All Films</h2>
  <p class="synopsis" style="margin-bottom: 32px; color: #aaa;">Every Fat Films original on one page. Click any title to read the full synopsis, cast list, and watch it.</p>
  <div class="grid">
{cards}
  </div>
</section>

{FOOTER}

{VERCEL_ANALYTICS}

</body>
</html>
"""


def render_about_page() -> str:
    head = render_head(
        "About Fat Films - AI Movie Parodies",
        "Fat Films recreates iconic scenes from popular films and series, making every character fat using cutting-edge AI. Millions of views across TikTok and Instagram.",
        "https://fatfilms.org/about",
        "https://fatfilms.org/titlecards/fat_club.jpg",
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
{head}
</head>
<body>

{NAV}

<section class="section" style="padding-top: 70px;">
  <h2 style="font-size: clamp(2.4rem, 5vw, 3.8rem); letter-spacing: 4px; margin-bottom: 12px;">About Fat Films</h2>
  <p class="synopsis" style="margin-bottom: 28px;">
    Fat Films is a viral AI entertainment project that recreates iconic scenes from
    legendary films and TV shows, reimagining every character as <strong>FAT</strong>
    using cutting-edge AI. From <em>American Psycho</em> to <em>Stranger Things</em>,
    <em>The Matrix</em> to <em>The Hunger Games</em>, no movie is safe from
    fatification.
  </p>
  <p class="synopsis" style="margin-bottom: 28px;">
    With millions of views across TikTok and Instagram, Fat Films has become one of
    the most popular AI video projects on the internet. We turn legendary movie
    moments into hilarious, larger-than-life masterpieces and ship them daily.
  </p>
  <p class="synopsis" style="margin-bottom: 28px;">
    Fat Films also has a community Solana token, <strong>$fatfilms</strong>, launched
    on Pumpfun. The token is community-driven and has no formal relationship to the
    creative project — it's just for the fans who want to share the fat love on-chain.
  </p>
  <div class="hero-actions" style="margin-top: 32px;">
    <a class="btn-primary" href="https://fatfilms.org">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
      Watch on fatfilms.org
    </a>
    <a class="btn-secondary" href="/films">Browse All Films</a>
    <a class="btn-secondary" href="/suggest">Suggest a Film</a>
  </div>
</section>

{FOOTER}

{VERCEL_ANALYTICS}

</body>
</html>
"""


def render_news_page() -> str:
    head = render_head(
        "News - Fat Films",
        "Latest news and updates from Fat Films. New releases, GIFs, and announcements.",
        "https://fatfilms.org/news",
        "https://fatfilms.org/gifscreenshot.jpg",
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
{head}
<style>
  .news-card {{
    background: #141414; border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px; padding: 32px; max-width: 800px; margin: 0 auto 36px;
  }}
  .news-card h3 {{
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.8rem; letter-spacing: 2px;
    color: #fff; margin-bottom: 14px;
  }}
  .news-card p {{ color: #ccc; line-height: 1.7; margin-bottom: 18px; }}
  .news-card .news-date {{ font-size: 0.78rem; color: #888; margin-bottom: 6px; }}
  .news-screenshot {{
    width: 100%; max-width: 480px; margin: 16px auto;
    display: block; border-radius: 8px;
    box-shadow: 0 6px 24px rgba(0,0,0,0.5);
  }}
  .news-gifs {{
    display: grid; grid-template-columns: 1fr 1fr;
    gap: 12px; margin-top: 18px;
  }}
  .news-gifs img {{ width: 100%; border-radius: 8px; box-shadow: 0 4px 16px rgba(0,0,0,0.5); }}
  @media (max-width: 640px) {{
    .news-card {{ padding: 22px; }}
    .news-gifs {{ grid-template-columns: 1fr; }}
  }}
</style>
</head>
<body>

{NAV}

<section class="section" style="padding-top: 60px;">
  <h2 style="font-size: clamp(2.2rem, 4vw, 3.2rem); letter-spacing: 3px; margin-bottom: 28px;">News</h2>

  <div class="news-card">
    <div class="news-date">April 2026</div>
    <h3>Fat Films GIFs are here!</h3>
    <p>
      You can now find Fat Films GIFs on Instagram and WhatsApp! Search
      <strong>'fatfilms'</strong> in the GIF section when messaging and our custom GIFs
      will appear. Share the fat love in your chats.
    </p>
    <img class="news-screenshot" src="/gifscreenshot.jpg" alt="Searching fatfilms in the GIF picker">
    <div class="news-gifs">
      <img src="/fatsogif.gif" alt="Fat Films GIF preview" loading="lazy">
      <img src="/wallstreetgif.gif" alt="Fat Films GIF preview" loading="lazy">
    </div>
  </div>

  <div style="text-align: center; margin-top: 40px;">
    <a class="btn-primary" href="https://fatfilms.org">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
      Watch on fatfilms.org
    </a>
  </div>
</section>

{FOOTER}

{VERCEL_ANALYTICS}

</body>
</html>
"""


def render_suggest_page() -> str:
    head = render_head(
        "Suggest a Film - Fat Films",
        "Vote for what film Fat Films should parody next. See the most requested films on the leaderboard.",
        "https://fatfilms.org/suggest",
        "https://fatfilms.org/titlecards/fat_club.jpg",
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
{head}
<style>
  .suggest-wrap {{ max-width: 720px; margin: 0 auto; }}
  .suggest-form {{ display: flex; gap: 10px; margin: 18px 0 10px; }}
  .suggest-form input {{
    flex: 1; padding: 14px 16px;
    border: 1px solid #2a2a2a; border-radius: 8px;
    background: #141414; color: #fff;
    font-size: 1rem; outline: none; font-family: inherit;
  }}
  .suggest-form input:focus {{ border-color: #555; }}
  .suggest-form button {{
    padding: 14px 28px; background: #e50914; color: #fff;
    border: none; border-radius: 8px; font-weight: 700;
    font-size: 1rem; cursor: pointer; font-family: inherit;
  }}
  .suggest-form button:disabled {{ opacity: 0.5; cursor: wait; }}
  .suggest-form button:hover:not(:disabled) {{ background: #f6121d; }}
  .msg {{ min-height: 1.2em; font-size: 0.95rem; margin-top: 8px; opacity: 0; transition: opacity 0.2s; }}
  .msg.show {{ opacity: 1; }}
  .msg.success {{ color: #7c7; }}
  .msg.error {{ color: #e06868; }}
  .msg.warn {{ color: #ffb347; }}
  .lb {{
    margin-top: 36px;
    display: flex; flex-direction: column; gap: 10px;
  }}
  .lb-item {{
    display: flex; align-items: center; gap: 14px;
    padding: 10px 14px;
    background: #141414; border: 1px solid rgba(255,255,255,0.06);
    border-radius: 8px;
  }}
  .lb-rank {{ font-family: 'Bebas Neue', sans-serif; font-size: 1.2rem; color: #888; width: 28px; text-align: center; }}
  .lb-poster {{ width: 44px; height: 66px; background: #222; border-radius: 4px; overflow: hidden; flex-shrink: 0; }}
  .lb-poster img {{ width: 100%; height: 100%; object-fit: cover; }}
  .lb-poster.empty {{ display: flex; align-items: center; justify-content: center; color: #444; font-size: 18px; }}
  .lb-title {{ flex: 1; font-size: 0.95rem; font-weight: 600; color: #e5e5e5; }}
  .lb-votes {{
    font-family: 'Space Mono', monospace; font-size: 0.78rem; color: #888;
    background: rgba(255,255,255,0.06); padding: 5px 12px; border-radius: 14px;
  }}
  .lb-empty {{ text-align: center; padding: 26px; color: #666; font-size: 0.9rem; }}
</style>
</head>
<body>

{NAV}

<section class="section" style="padding-top: 60px;">
  <div class="suggest-wrap">
    <h2 style="font-size: clamp(2.2rem, 4vw, 3.2rem); letter-spacing: 3px;">Suggest a Film</h2>
    <p class="synopsis" style="font-size: 1rem; color: #aaa; margin: 14px 0 4px;">What film do you want to see <strong style="color:#fff;">FAT</strong>?</p>
    <div class="suggest-form">
      <input id="suggest-input" type="text" placeholder="e.g. The Dark Knight, Breaking Bad...">
      <button id="suggest-btn">Submit</button>
    </div>
    <div id="suggest-msg" class="msg"></div>

    <h3 style="font-family: 'Bebas Neue', sans-serif; font-size: 1.4rem; letter-spacing: 2px; margin: 36px 0 14px; color: #fff;">Top Suggestions</h3>
    <div id="lb" class="lb"><div class="lb-empty">Loading...</div></div>
  </div>
</section>

{FOOTER}

<script>
const lbEl = document.getElementById('lb');
const inputEl = document.getElementById('suggest-input');
const btnEl = document.getElementById('suggest-btn');
const msgEl = document.getElementById('suggest-msg');

function esc(s) {{
  return String(s).replace(/[&<>"']/g, c => ({{
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }}[c]));
}}
function showMsg(text, kind) {{
  msgEl.textContent = text;
  msgEl.className = 'msg show ' + kind;
  clearTimeout(showMsg._t);
  showMsg._t = setTimeout(() => msgEl.classList.remove('show'), 5000);
}}

function renderLB(items) {{
  if (!items || items.length === 0) {{
    lbEl.innerHTML = '<div class="lb-empty">No suggestions yet — be the first.</div>';
    return;
  }}
  lbEl.innerHTML = items.slice(0, 20).map((it, i) => {{
    const poster = it.poster_url
      ? `<div class="lb-poster"><img src="${{esc(it.poster_url)}}" alt="" loading="lazy"></div>`
      : '<div class="lb-poster empty">&#127916;</div>';
    return `<div class="lb-item">
      <div class="lb-rank">${{i+1}}</div>
      ${{poster}}
      <div class="lb-title">${{esc(it.title || 'Untitled')}}</div>
      <div class="lb-votes">${{it.vote_count}} vote${{it.vote_count === 1 ? '' : 's'}}</div>
    </div>`;
  }}).join('');
}}

async function loadLeaderboard() {{
  try {{
    const r = await fetch('/api/leaderboard');
    if (!r.ok) throw new Error('fail');
    const d = await r.json();
    renderLB(d.suggestions);
  }} catch {{
    lbEl.innerHTML = '<div class="lb-empty">Couldn\\u2019t load leaderboard.</div>';
  }}
}}

async function submitSuggest() {{
  const title = inputEl.value.trim();
  if (!title) return;
  btnEl.disabled = true; btnEl.textContent = 'Sending...';
  try {{
    const r = await fetch('/api/suggest', {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/json' }},
      body: JSON.stringify({{ title }})
    }});
    const d = await r.json().catch(() => ({{}}));
    if (r.ok && d.success) {{
      showMsg('\\u2705 Added \\u201C' + d.title + '\\u201D to the leaderboard', 'success');
      inputEl.value = '';
      if (Array.isArray(d.leaderboard)) renderLB(d.leaderboard);
      else loadLeaderboard();
    }} else {{
      showMsg(d.error || 'Something went wrong. Try again.', 'error');
    }}
  }} catch {{
    showMsg('Network error. Try again.', 'error');
  }} finally {{
    btnEl.disabled = false; btnEl.textContent = 'Submit';
  }}
}}

btnEl.addEventListener('click', submitSuggest);
inputEl.addEventListener('keydown', e => {{ if (e.key === 'Enter') submitSuggest(); }});
loadLeaderboard();
</script>

{VERCEL_ANALYTICS}

</body>
</html>
"""


def render_sitemap(films: list[dict]) -> str:
    today = "2026-05-17"
    urls = [
        ("https://fatfilms.org", "1.0"),
        ("https://fatfilms.org/films", "0.8"),
        ("https://fatfilms.org/suggest", "0.8"),
        ("https://fatfilms.org/about", "0.8"),
        ("https://fatfilms.org/news", "0.8"),
    ]
    for f in films:
        urls.append((f"https://fatfilms.org/films/{url_slug(f)}", "0.6"))

    entries = "\n".join(
        f"  <url>\n    <loc>{loc}</loc>\n    <lastmod>{today}</lastmod>\n    <priority>{pri}</priority>\n  </url>"
        for loc, pri in urls
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{entries}
</urlset>
"""


def main() -> None:
    for i, film in enumerate(FILMS):
        recs = pick_recommendations(FILMS, i, n=4)
        (FILMS_DIR / f"{url_slug(film)}.html").write_text(
            render_film_page(film, recs), encoding="utf-8"
        )
    (FILMS_DIR / "index.html").write_text(render_films_hub(FILMS), encoding="utf-8")
    (PUBLIC / "about.html").write_text(render_about_page(), encoding="utf-8")
    (PUBLIC / "news.html").write_text(render_news_page(), encoding="utf-8")
    (PUBLIC / "suggest.html").write_text(render_suggest_page(), encoding="utf-8")
    (PUBLIC / "sitemap.xml").write_text(render_sitemap(FILMS), encoding="utf-8")

    print(f"Wrote {len(FILMS)} film pages + 4 hub pages + sitemap.")


if __name__ == "__main__":
    main()
