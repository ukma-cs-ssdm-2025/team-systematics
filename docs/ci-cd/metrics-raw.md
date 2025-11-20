# Pages-build-deployment:
## Гілка main
- Кількість успішних розгортань (deployment frequency) - 6
- Середній час від коміту до зеленого білду (lead time) - 44,5 s.
- Частота збоїв (change failure rate) - 0% (не було збоїв)
- Середній час відновлення після збою (time to restore) - 0 (не було збоїв)

| Run # | Commit SHA | Status | Start → End (min) | Deployed? | Notes |
|:-----:|------------|:------:|:-----------------:|:---------:|:------|
| 1     |4d2279a     | ✅     | 48s              | ✅        |       |
| 2     |c57f66f     | ✅     | 41s              | ✅        |       |
| 3     |6b35e2e     | ✅     | 45s              | ✅        |       |
| 4     |5e38194     | ✅     | 44s              | ✅        |       |
| 5     |6d119d3     | ✅     | 45s              | ✅        |       |
| 6     |db86e32     | ✅     | 44s              | ✅        |       |


# Run Api Tests:
## Гілка main
- Кількість успішних розгортань (deployment frequency) - 5
- Середній час від коміту до зеленого білду (lead time) - 2m 17,4s
- Частота збоїв (change failure rate) - 50%
- Середній час відновлення після збою (time to restore) - 1 h

| Run # | Commit SHA | Status | Start → End (min) | Deployed? | Notes         |
|:-----:|------------|:------:|:-----------------:|:---------:|:--------------|
| 1     |9defe83     | ✅     | 2m 1s            | ✅        |               |
| 2     |445a7db     | ✅     | 2m 24s           | ✅        |               |
| 3     |87940d0     | ✅     | 2m 13s           | ✅        |               |
| 4     |3551270     | ✅     | 2m 11s           | ✅        |               |
| 5     |0bc06a8     | ✅     | 2m 38s           | ✅        |               |
| 6     |c357573     | ❌     | 2m 9s            | ❌        |unit test fail |
| 7     |8d3a634     | ❌     | 2m 50s           | ❌        |unit test fail |
| 8     |8e17fbb     | ❌     | 2m 3s            | ❌        |unit test fail |
| 9     |17f9307     | ❌     | 2m 6s            | ❌        |unit test fail |
| 10    |97020b8     | ❌     | 39s              | ❌        |unit test fail |


# CI Test:
## гілка main
- Кількість успішних розгортань (deployment frequency) - 10
- Середній час від коміту до зеленого білду (lead time) - 8.1c
- Частота збоїв (change failure rate) - 0% (не було збоїв)
- Середній час відновлення після збою (time to restore) - 0 (не було збоїв)

| Run # | Commit SHA | Status | Start -> End (min) | Deployed? | Notes |
|-------|------------|--------|-------------------|------------|-------|
| 1     | 9defe83    | ✅     | 7s                | ✅        |       |
| 2     | 445a7db    | ✅     | 10s               | ✅        |       |
| 3     | 87940d0    | ✅     | 6s                | ✅        |       |
| 4     | 3551270    | ✅     | 7s                | ✅        |       |
| 5     | 0bc06a8    | ✅     | 9s                | ✅        |       |
| 6     | c357573    | ✅     | 9s                | ✅        |       |
| 7     | 8d3a634    | ✅     | 12s               | ✅        |       |
| 8     | 8e17fbb    | ✅     | 8s                | ✅        |       |
| 9     | 17f9307    | ✅     | 6s                | ✅        |       |
| 10    | 97020b8    | ✅     | 7s                | ✅        |       |


# Deploy Docs to GitHub Pages:
# гілка main
- Кількість успішних розгортань (deployment frequency) - 6
- Середній час від коміту до зеленого білду (lead time) - 17.3s
- Частота збоїв (change failure rate) - 0% (не було збоїв)
- Середній час відновлення після збою (time to restore) - 0 (не було збоїв)

| Run # | Commit SHA | Status | Start -> End (min) | Deployed? | Notes |
|-------|------------|--------|-------------------|------------|-------|
| 1     | 2e9d43b    | ✅     | 15s               | ✅        |       |
| 2     | 766f677    | ✅     | 15s               | ✅        |       |
| 3     | 4d2279a    | ✅     | 17s               | ✅        |       |
| 4     | 6ee8e17    | ✅     | 16s               | ✅        |       |
| 5     | 8f93df1    | ✅     | 18s               | ✅        |       |
| 6     | b84f1e5    | ✅     | 23s               | ✅        |       |


# Generate plantuml:
# гілка main
- Кількість успішних розгортань (deployment frequency) - 6
- Середній час від коміту до зеленого білду (lead time) - (немає даних, останній фейлиться)
- Частота збоїв (change failure rate) - 14%
- Середній час відновлення після збою (time to restore) - (немає даних, усе ще не виправлено)

| Run # | Commit SHA | Status | Start -> End (min) | Deployed? | Notes                                                 |
|-------|------------|--------|-------------------|------------|-------------------------------------------------------|
| 1     | 888c4e1    | ❌     | 10s               | ❌        |HttpError: Changes must be made through a pull request |
| 2     | 7921f4d    | ✅     | 8s                | ✅        |                                                       |
| 3     | 672e3f5    | ✅     | 9s                | ✅        |                                                       |
| 4     | b43c25c    | ✅     | 8s                | ✅        |                                                       |
| 5     | 8078189    | ✅     | 10s               | ✅        |                                                       |
| 6     | 770be24    | ✅     | 10s               | ✅        |                                                       |
| 7     | 9398069    | ✅     | 13s               | ✅        |                                                       |

# Generate and Auto-Merge API Docs:
# гілка main
- Кількість успішних розгортань (deployment frequency) - 10
- Середній час від коміту до зеленого білду (lead time) - Немає даних
- Частота збоїв (change failure rate) - 100%
- Середній час відновлення після збою (time to restore) - Немає даних

| Run # | Commit SHA | Status | Start -> End (min) | Deployed? | Notes                         |
|-------|------------|--------|--------------------|-----------|-------------------------------|
| 1     | 9defe83    | ❌     | 1m 55s            | ❌        | Database type incompatibility |
| 2     | 445a7db    | ❌     | 2m 15s            | ❌        | Database type incompatibility |
| 3     | 87940d0    | ❌     | 3m 20s            | ❌        | Database type incompatibility |
| 4     | 3551270    | ❌     | 1m 48s            | ❌        | Database type incompatibility |
| 5     | 0bc06a8    | ❌     | 2m 18s            | ❌        | Database type incompatibility |
| 6     | c357573    | ❌     | 2m 8s             | ❌        | Database type incompatibility |
| 7     | 8d3a634    | ❌     | 2m 3s             | ❌        | Database type incompatibility |
| 8     | 8e17fbb    | ❌     | 1m 59s            | ❌        | Database type incompatibility |
| 9     | 17f9307    | ❌     | 2m 52s            | ❌        | Database type incompatibility |
| 10    | 97020b8    | ❌     | 33s               | ❌        | Database type incompatibility |
