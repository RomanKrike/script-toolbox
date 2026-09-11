# ConfigStore и отложенное сохранение Runtime

Runtime-значения Script Toolbox могут генерировать много событий изменения за короткий промежуток. Основной пример — Integer/Float spin boxes: перетаскивание или пошаговое изменение значения может создать последовательность сигналов `valueChanged`.

До STEP 04 каждое изменение сразу вызывало `save_config()`. Так как запись конфигурации сериализует весь toolbox document, flush, `fsync()`, ротацию backup и атомарную замену основного JSON, короткое взаимодействие могло приводить к множеству полных записей на диск.

## Контракт persistence

`core/config_store.py` владеет host-independent состоянием persistence:

- текущим связанным document;
- признаком dirty;
- настроенным writer/path;
- синхронными `flush()` и явным `save()`;
- dirty state остаётся установленным при ошибке записи.

`ConfigStore` намеренно не владеет worker thread или Qt object.

Активный Runtime Maya/Nuke использует single-shot `QTimer` на главном DCC-thread с интервалом 500 ms. Изменения через Runtime `store_value()` помечают store как dirty и перезапускают timer. Поэтому серия value events схлопывается в одну запись config после завершения взаимодействия.

## Немедленное сохранение

Публичное поведение `toolbox.save()` остаётся синхронным. Interface Editor Apply/Accept и другие явные вызовы сохраняют прежний durability contract.

Debounce используется только для persistence, возникающего из Runtime `store_value()`.

## Обязательные точки flush

Ожидающие изменения записываются перед:

1. reload конфигурации;
2. development module reload;
3. началом установки updater;
4. updater hot reload;
5. закрытием toolbox/window.

Если обязательный flush завершается ошибкой, `ConfigStore` остаётся dirty. Переходы close/reload/update по возможности останавливаются вместо молчаливой потери ожидающих in-memory values.

Ошибки записи, вызванной timer, показываются в status bar и могут быть повторены при следующем изменении или явном lifecycle flush.

## Правило DCC/threading

Не переносите сохранение config в фоновый Python thread только ради уменьшения UI stalls. Lifecycle Maya 2015/Python 2.7 и Nuke усложняет teardown/error handling в фоне, а backup и replace уже являются короткими ограниченными filesystem transactions.

Текущий дизайн уменьшает частоту записей, сохраняя persistence на главном DCC-thread. В будущем разделение toolbox definition и per-user runtime state может дополнительно уменьшить размер сериализации без изменения этого debounce-контракта.
