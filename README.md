# Snake AI
Python Snake game with neural network (NEAT) AI

## Dependencies
```shell script
pip install -r requirements.txt
```

## Usage

Start learning from scratch
```python
python snake.py
```

or use previously saved population
```python
python snake.py population.dat
```

Press space to toggle fast mode - speed will be reduced to 10 fps and you will see network outputs in the console.

After exceeding fitness threshold (fitness_threshold in config.txt) the population is saved in population.dat file.

You can comment out redraw function (line 196) to speed up learning process.

If you want to play the game by yourself, just comment out line 182 and uncomment lines 128-131 and 185-186.