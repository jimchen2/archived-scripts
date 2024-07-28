
## 3x3 grids 2048

## Play

```
python simulate_behavioral_cloning.py
```

## Simple Behavioral Cloning

1. Self play(low performance) around n=100 rounds, then throwing away all data where max tiles is below 128
```
Number of games analyzed: 54
Average max tile: 173.04
Highest max tile: 256
Lowest max tile: 128
Average number of moves: 130.11
Average final score: 287.41

Max tile distribution:
  128: 35 times (64.81%)
  256: 19 times (35.19%)
```
2. Duplicate each into 4 making 4n rounds(rotate it)
3. Throw away first 20 or 30 moves in each round. This is because I was moving randomly at the start.

### Network

We use a simple network, with 3 paralleled CNN: 1x2, 2x1 and 2x2, and identity, passed to linear layers

The final average max tile is 117.

The performance is good since I am very suboptimal player, and I threw away like half to 1/3 of the performances and kept only the ones that got 128 or 256.


If we add the good performances in evalution back to dataset (e.g. performance that got final tiles 512 and 256+128 from simulation), and the result only got a lot worse(with average max tile around 85). If we only add 6 good performance in evaluation that got 512 back the best performance was final max tile average 111. The model is exploting on the same data, which won't make it better. It is quite intuitive.


<video src="https://public.jimchen.me/save/Screencast%20from%202024-07-28%2015-59-26.webm" controls>

</video>
