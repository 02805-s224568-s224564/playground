---
title: "Who links out, who gets linked?"
week: 1
authors: ["Johan Holmsteen", "Joes Hasselriis Nicolaisen"]
notebook: notebooks/week1-networks.ipynb
---

Does the ratio between a character's in- and out-degree tell a story about how famous they are? As it turns out, no — but it is not obvious why.

## What we asked

Do famous characters mainly have Wikipedia articles about themselves, while obscure characters mainly tell their story through their relationships to better-known characters? If so, we should see well-known characters with a higher in-degree than out-degree, and the reverse for obscure ones.

## What we did

We took the ten articles with the highest in-degree and the ten with the highest out-degree, and made a subjective check of whether we had heard of each character. In addition, we calculated the ratio between in- and out-degree to see whether it could act as an indicator of fame and obscurity.

## What we found

Top 10 by in-degree (linked to most):

| name                      | in  | out |
| ------------------------- | --- | --- |
| Spider-Man                | 106 | 9   |
| Hulk                      | 64  | 10  |
| Wolverine (character)     | 60  | 17  |
| Doctor Strange            | 50  | 17  |
| Deadpool                  | 33  | 19  |
| She-Hulk                  | 29  | 20  |
| Scarlet Witch             | 28  | 14  |
| Black Panther (character) | 27  | 11  |
| Cyclops (Marvel Comics)   | 26  | 11  |
| Luke Cage                 | 25  | 9   |

The table does seem to bear this out: a famous character has many articles linking to it and fewer links going out.

Top 10 by out-degree (link out most):

| name                          | in  | out |
| ----------------------------- | --- | --- |
| Betsy Braddock                | 7   | 28  |
| Cloak and Dagger (characters) | 11  | 24  |
| Adam Warlock                  | 8   | 22  |
| Venom (character)             | 17  | 21  |
| She-Hulk                      | 29  | 20  |
| U.S. Agent                    | 6   | 20  |
| Deadpool                      | 33  | 19  |
| Rachel Summers                | 16  | 19  |
| Noh-Varr                      | 4   | 18  |
| Doctor Strange                | 50  | 17  |

Venom, Deadpool, Doctor Strange and She-Hulk all turn up here. These characters are well known, and they break the idea of a high out-degree alone being an indicator of obscurity.

## What surprised us

Spider-Man and Betsy Braddock each fit one side of our hypothesis, but the inclusion of the well-known characters Venom, Doctor Strange and Deadpool breaks it.
