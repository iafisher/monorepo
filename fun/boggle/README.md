A Python implementation of the board game [Boggle](https://en.wikipedia.org/wiki/Boggle).

```shell
$ boggle
$ boggle --duration 300
$ boggle --size 5
```

The program ships with two English-language dictionaries, `words/en.txt` and `words/en_abridged.txt`. By default, the latter is used, but you can use the full dictionary like so:

```shell
$ boggle --words words/en.txt
```

The abridged dictionary excludes words that I subjectively deem marginal.
