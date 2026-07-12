# 最終再実行結果

## 修正owner / mandatory two-stage / withdrawal

`277 passed, 1 warning, 41 subtests passed in 15.31s`

## public API / public feedback / display boundary

`130 passed, 1 warning in 14.40s`

## I0 inventory + I1 GroundedObservationPlan

`29 passed, 1 warning in 24.85s`

## compileall

`PASS`

## Warning

`api_emotion_submit.py` の既存Pydantic V1 `@root_validator` deprecation warning 1件。今回の修正起因ではありません。

## 未完了

全 `ai/tests` のmonolithic collectは600秒timeoutで完了していません。したがって全backend suite完走とは主張しません。
