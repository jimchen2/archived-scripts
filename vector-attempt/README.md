## Database

```
-- Create extension (you may need to install pgvector package first)
CREATE EXTENSION IF NOT EXISTS vector;

-- Create a documents table with vector embeddings
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255),
    content TEXT,
    language VARCHAR(50),
    embedding vector(384)  -- Using 384 dimensions (typical for sentence-transformers)
);

-- Create index for faster similarity search
CREATE INDEX ON documents USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

## Documents

```
(.venv) user@fedora ~/Downloads> cat doc1|head -n 1
Росси́я, или Росси́йская Федера́ция[e] (сокр. РФ[f]), — государство в Восточной Европе и Северной Азии. Россия — крупнейшее государство в мире, её территория в международно признанных границах составляет 17 098 246 км²[22]. Население страны вместе с аннексированным Крымом, переданным из РСФСР в УССР в 1954 году, являющийся после захвата Россией спорной территорией[23], составляет 146 119 928[14] человек (2025; 9-е место в мире). Столица — Москва. Государственный язык на всей территории страны — русский, в ряде регионов России также установлены свои государственные[24] и официальные языки. Денежная единица — российский рубль.
(.venv) user@fedora ~/Downloads> cat doc2|head -n 1
The United States of America (USA), also known as the United States (U.S.) or America, is a country primarily located in North America. It is a federal republic of 50 states and a federal capital district, Washington, D.C. The 48 contiguous states border Canada to the north and Mexico to the south, with the semi-exclave of Alaska in the northwest and the archipelago of Hawaii in the Pacific Ocean. The United States also asserts sovereignty over five major island territories and various uninhabited islands in Oceania and the Caribbean.[j] It is a megadiverse country, with the world's third-largest land area[c] and third-largest population, exceeding 340 million.[k]
(.venv) user@fedora ~/Downloads> cat doc3 |head -n 1
The Three Gorges Dam,[a] officially known as Yangtze River Three Gorges Water Conservancy Project[b] is a hydroelectric gravity dam that spans the Yangtze River near Sandouping in Yiling District, Yichang, Hubei province, central China, downstream of the Three Gorges. The world's largest power station by installed capacity (22,500 MW),[5][6] the Three Gorges Dam generates 95±20 TWh of electricity per year on average, depending on the amount of precipitation in the river basin.[7] After the monsoons of 2020, the dam produced nearly 112 TWh in a year, breaking the record of 103 TWh set by the Itaipu Dam in 2016.[8][9]
(.venv) user@fedora ~/Downloads> cat doc4 |head -n 1
Yosemite National Park (/joʊˈsɛmɪti/ yoh-SEM-ih-tee[5]) is a national park of the United States in California.[6][7] It is bordered on the southeast by the Sierra National Forest and on the northwest by Stanislaus National Forest. The park is managed by the National Park Service and covers 1,187 sq mi (3,070 km2)[3] in four counties – centered in Tuolumne and Mariposa, extending north and east to Mono and south to Madera. Designated a World Heritage Site in 1984, Yosemite is internationally recognized for its granite cliffs, waterfalls, clear streams, groves of giant sequoia, lakes, mountains, meadows, glaciers, and biological diversity.[8] Almost 95 percent of the park is designated wilderness.[9] Yosemite is one of the largest and least fragmented habitat blocks in the Sierra Nevada mountain range.
(.venv) user@fedora ~/Downloads>
```

## Insert

```
user@fedora ~/Downloads> source ~/.venv/bin/activate.fish
pip install psycopg2-binary sentence-transformers pgvector
```

```
(.venv) user@fedora ~/Downloads> python populate_vectors.py 
Inserted: Russia Wikipedia
Inserted: USA Wikipedia
Inserted: Three Gorges Dam Wikipedia
Inserted: Yosemite National Park Wikipedia
```
