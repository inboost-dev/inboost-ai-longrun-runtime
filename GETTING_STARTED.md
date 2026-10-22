# Getting Started & Интерактивные Демо
## InBoost LongRun Evaluation Runtime (`inboost-longrun`)

> **Назначение:** Быстрый запуск за 2 минуты, сценарии оффлоада инструментов на CPU хоста (0 токенов в подписке), MCP-сервер для Claude Code и Cursor, воспроизведение бенчмарков.  
> **Официальный домен:** `https://inboost.pro` • **Лицензия:** Evaluation License

---

## ⚡ 2-Строчный Быстрый Старт (Zero-Friction Setup)

InBoost LongRun работает прямо на вашей рабочей станции и не требует сложной конфигурации:

### Вариант А. Мгновенно через `npx` (Без предварительной установки)
```bash
# Автоматическая настройка правил для Claude Code, Cursor и Antigravity
npx @inboost-pro/inboost-longrun init

# Проверка окружения и доступных инструментов offload
npx @inboost-pro/inboost-longrun doctor
```

### Вариант Б. Глобальная установка через npm или pip
```bash
# Через npm
npm install -g @inboost-pro/inboost-longrun
inboost-longrun init
inboost-longrun doctor

# Или через Python pip
pip install inboost-longrun
inboost-longrun init
```

Команда `init` автоматически:
1. Регистрирует оптимизационные правила в `~/.claude/rules/inboost_longrun.md` и `.cursorrules`.
2. Подключает MCP-сервер `inboost-longrun` в `.cursor/mcp.json`.
3. Настраивает лимиты диффов ($\le 180$ строк) и директивы сохранения синтаксиса.

---

## 🎮 Демо 1: Host-акселератор в действии (Оффлоад инструментов на CPU)

> **Суть демонстрации:** Показать, почему инструменты разработчика (`grep`, `ast`, `pytest`) должны выполняться на локальном процессоре бесплатно (**0 токенов в подписке**), а не расходовать дорогую квоту облачных нейросетей.

### Симуляция сбоя тестов:
Выполните тестовую команду через обертку LongRun:

```bash
inboost-local run pytest tests/
```

### Что происходит на экране:
```text
[InBoost L0 Engine] Executing: pytest tests/ ...
[InBoost L0 Engine] Failure intercepted: 8,420 lines of raw traceback detected.
[TracebackCrusher] Compressing stack traces on Host CPU in 11.4 ms...
  ├── Filtered: pluggy/runner.py (3,800 lines of library noise)
  ├── Filtered: _pytest/assertion/rewrite.py (2,900 lines of boilerplate)
  └── Pinpointed AST Range: src/core/parser.py:L142-L144 (ast.NameConstant fix)
[InBoost L0 Engine] Result: 8,420 lines -> 38 lines (-95.5% noise reduction).
[Quota Status] 0 TOKENS BILLED IN CLOUD SUBSCRIPTION.
```

В модель попадает только точечный контекст сбоя (38 строк вместо 8 420 строк), а разработчик не расходует квоту сообщений.

---

## 🎮 Демо 2: Предотвращение пустых патчей (Pre-Commit Ultimatum)

> **Суть демонстрации:** В стандартном режиме 70% открытых моделей сдаются и отдают пустой дифф (0 байт), когда не могут локализовать ошибку. LongRun детерминистически блокирует сдачу пустого результата.

```bash
# Запуск симулятора арбитража LongRun
inboost-longrun check-diff --strict
```

### Механика работы:
1. Если агент пытается вызвать завершающую команду (`submit`), не внеся изменений в код, срабатывает **Pre-Commit Ultimatum**.
2. Агенту возвращается жесткая директива: *«Сдача с 0 байт запрещена. На основе локализованного AST-узла в файле X примени минимальный дифф до 20 строк»*.
3. **Результат:** 100% ликвидация пустых патчей (на SWE-bench Verified $N=500$ показатель 0B-патчей снизился с 7.4% до **0.00%**).

---

## 🎮 Демо 3: Подключение как MCP-сервер в Claude Code

InBoost LongRun нативно поддерживает протокол **Model Context Protocol (MCP)**.

### Добавление сервера в Claude Code:
```bash
claude mcp add inboost-longrun -- npx @inboost-pro/inboost-longrun serve
```

После регистрации Claude Code получает 4 субмиллисекундных инструмента прямо на CPU ноутбука:

| MCP-Инструмент | Назначение | Экономия токенов |
| :--- | :--- | :---: |
| `l0_clean_test_log` | Сжатие сырого вывода pytest/vitest до точки падения | **-86% … -95%** |
| `l0_view_outline` | Вывод скелета классов и функций без чтения тела (14 мс) | **-98%** |
| `l0_verify_syntax` | Мгновенная проверка валидности AST до сохранения файла | **0 сбоев синтаксиса** |
| `l0_verify_edit_scope` | Контроль бюджета правок ($\le 180$ строк) | **Защита от овер-диффов** |

---

## 🎮 Демо 4: Автономный ночной прогон пакета задач (Batch SWE-bench)

LongRun может автономно решать очереди задач в фоновом режиме:

```bash
# Запуск автономного прогона когорты из 10 задач SWE-bench с Claude Code
inboost-longrun --batch benchmarks/cohorts/cohort_random_25.json \
  --agent claude-code \
  --max-workers 2 \
  --output runs/batch_evaluation_$(date +%Y%m%d)/
```

По завершении прогона автоматически генерируется скоркард:
- Доля решенных задач (Pass@1);
- Объем сэкономленных токенов на Host CPU;
- Время решения на каждый тикет;
- Готовые диффы в каталоге `runs/latest/patches/`.

---

## 🔗 Связанные материалы
- 📊 **[Регламент публикации бенчмарков](BENCHMARKS.md)**: Стандарты достоверности, Docker-тестирование и официальные результаты ($N=25$, $N=500$).
- 📈 **[Подробный скоркард N=25](benchmarks/SCORECARD.md)**: Позадачная телеметрия и результаты прогона.
- 🌐 **[Официальный портал платформы](https://inboost.pro)**: Документация и коммерческая лицензия InBoost Pro.
