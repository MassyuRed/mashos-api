# MashOS Module Architecture (Release-aligned)

本書は、機能ごと（Input / Web / Flower / AI）の責務境界を明確化し、命名の整合を取るための整理図です。

```mermaid
flowchart TD
  subgraph App[React Native App]
    InputScreen -->|save| Supabase[(Supabase: emotions)]
    MyWebScreen -->|read| Supabase
    MyModelScreen -->|POST /mymodel/infer| API[(FastAPI app.py)]
    Unity[Unity 花の世界] <-->|render state| FlowerCore
  end

  subgraph MashOS Core (TS)
    InputCore[inputCore.ts] -->|buildEntry()| types[types.ts]
    MyWebCore[mywebCore.ts] -->|period APIs| types
    FlowerCore[flowerCore.ts] -->|annotate/analyze| types
    TimeSvc[timeService.ts] -->|MashTime| types
    Index[index.ts] -->|MashOS.{input,myweb,flower}| App
  end

  API -->|stateless infer| MyModelAI[Cocolon MyModel API]
  FlowerCore -->|toneColor/shape/animation, climate| Unity
```

## 境界の要点
- **Flower** は視覚演出専用（`annotate` / `analyze`）。AI応答（テキスト）は扱わない。
- **AI(MyModel)** は `app.py` の FastAPI が担う（`/mymodel/infer`）。
- **MyWeb** は週報・月報などの期間計算のみ。
- **Input** は感情入力を構造化して Supabase へ保存。
- **TimeService** は各機能ごとに *off/snapshot/interval* を提供。

