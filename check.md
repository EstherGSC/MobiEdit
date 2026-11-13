# 任务：核对 MobiEdit 代码是否实现了论文的每个机制

## 背景
- 基底是 ROME，MobiEdit 在它之上组合了 4 个机制：**ZO 无 BP 编辑**、**混合精度量化**、**早停**、**前缀激活复用**。
- 我只需要确认"每个机制是否被正确实现 + 是否可由 yaml 开关控制"，**不需要跑实验，不需要装 bitsandbytes，不需要改代码**（除非发现明确 bug，改前先报告）。
- 判定标准以 `MobiEdit.pdf` 和 `ME.md` 为准，逐条对齐公式与 §2.x 描述。

## 输出格式
对下面每个机制，按模板输出：

```
### 机制 X：<名称>
- 论文要求：<一句话，附 §节号/公式号>
- 代码位置：<文件:行号>
- 配置入口：<yaml 字段名，或"无"（写死）>
- 判定：✅ 符合 / ⚠️ 部分符合 / ❌ 未实现 / ❓ 无法确认（需模型侧/外部代码）
- 证据：<3–5 行关键代码>
- 与论文差异：<有则列，无则写"无">
- 修复建议：<最小改动，只针对 yaml 或 run 副本>
```

最后给一张汇总表 + 一份"最小可跑 yaml"。

---

## 一、ROME 基线（基底）
1. `compute_u` 是否按 ROME 原式 $u = \frac{C^{-1}k_*}{\|C^{-1}k_*\|}$ 计算？`C = KK^T` 是否用 `mom2` 统计量（`stats_dir` / `mom2_dataset`）正确构造？
2. `compute_v`（BP 版）是否仍保留、未被 ZO 分支破坏？
3. `apply_rome_to_model` 里 `w[...] += upd_matrix` 是否对**原始 parameter 做 in-place 更新**（不是 `w = w.to(...)` 重新绑定）？
4. `upd_matrix_match_shape` 是否处理了转置与 reshape？

## 二、ZO 无 BP 编辑（论文 §2.2，公式 1/2）
5. **公式 (2) 的 `1/N`**：`forward_grad_step` 里 `grad_est` 是否除以 `v_nums`？`v_nums` 是多少（论文 ablation 用 5）？
6. **中心差分**：`calculate_jvp` 是否用 $\frac{L(\delta+hu)-L(\delta-hu)}{2h}$，`h = zo_eps`？
7. **重复前向**：`f(δ)` 是否每个方向都重算？若是，说明多算了 `N-1` 次前向，记为 ⚠️（论文强调前向次数直接决定能效）。
8. **更新式**：`delta -= lr * grad_est`，`lr` 是否走余弦退火（`_get_learning_rate`）？论文 Appendix D 明确说余弦退火让 N=5 可用、静态 lr 需要 N=300。
9. **L2 投影**：是否 `||delta|| <= clamp_norm_factor * ||target_init||`。
10. **yaml 开关**：`use_zo: true/false` 是否真的在 `rome_main.execute_rome` 里分流到 `compute_v_zo` / `compute_v`。
11. **死代码**：`forward_grad_step_hessian / _zoadamu / _choosev / _para`、`zo_step` 是否被主流程调用？未被调用则标注"实验变体，保留不影响主流程"。

## 三、混合精度量化（论文 §2.3）
12. **格式**：`W8A16Model` 是否真的 INT8 权重 + INT16 激活（还是 INT8/INT8 或 fake-quant）？给出 weight/act 的量化 dtype。
13. **静态 scale**：`calibrate()` 是否真的更新 scale（非空操作）？打印 1 个模块 calibrate 前后的 scale 值佐证。
14. **校准数据**：`compute_v_zo` 里 `quan_model.calibrate(input_tok)` 用的是**编辑输入本身**。论文要求 representative corpora → 记 ⚠️，并给"换成 WikiText 小样本"的最小改动。
15. **skip_modules**：`compute_v_zo` 里是否硬编码 `["model.layers.5.mlp.down_proj"]`？若 `hparams.layers != [5]` 会 skip 错层 → 记 ❌，建议改 `hparams.mlp_module_tmp.format(layer) + ".down_proj"`。
16. **skip 语义**：论文要求"编辑向量 + 其 preceding linear layer"保持 float。确认 `delta` 注入位置（`down_proj` 输出）与 skip 是否一致。
17. **量化精度验收**：`compute_v` 里 `before_quan_logits` vs `after_quan_logits` 的 cos_sim 打印是否保留？阈值 > 0.99（论文隐含）。
18. **yaml 开关**：`quantize: true/false` 是否真的控制 `W8A16Model` 的启用。
19. **编辑器层干扰**：`editor.py` 的 `AutoModelForCausalLM.from_pretrained` 是否传了 `load_in_8bit=True` 或 `quantization_config=BitsAndBytesConfig(...)`？若有 → ❌（与 W8A16Model 冲突，且 bnb Int8Params 无法做 rank-1 加法），建议删除。

## 四、早停（论文 §2.4，Figure 3）
20. **周期评估**：`compute_v_zo` 里是否每 `M` 步做一次"插入 → `compute_edit_quality` → 恢复"？`M` 是否可由 yaml 配（`early_stop_eval_steps`，论文示例 20）？
21. **成功判据**：`rewrite_acc` 是否用阈值判定（`early_stop_threshold`，论文提到 confidence 阈值 m）？阈值默认多少？
22. **触发后行为**：是否 `break` 并正确写 `hparams.last_steps = it + 1`？是否打 `EARLY_STOP triggered_at_step=... reason=edit_success`？
23. **loss 阈值兜底**：`loss < 1e-5` 的 break 是否保留？两者是否都记入 `last_steps`。
24. **评估开销**：`compute_edit_quality(..., test_generation=True)` 是否每次早停都跑？论文只需 exact match → 记 ⚠️，建议 `test_generation=False`。
25. **重复恢复评估**：早停恢复后是否又调一次 `compute_edit_quality` 做 `Restore succ`？论文无此步 → 记 ⚠️，建议注释或加开关。
26. **配置入口**：yaml 是否有 `early_stop_eval_steps` / `early_stop_threshold` 字段？若无则走 `getattr(..., 默认)`，写死在代码。

## 五、前缀激活复用（论文 §2.4，Figure 5）
27. **固定前缀集**：`compute_v_zo` 的 `context_templates` 是否在一次编辑的**所有优化步中保持不变**？（对比 `compute_v_randomprefix_zo` 每步重采样——那是消融，不是主方法）。
28. **缓存机制**：`ZOTrainer` 是否在 `__init__` 里 `_clear_prefix_cache()`，并在 `zero_order_loss` 里通过 `prefix=10` 触发缓存复用？
29. **刷新触发**：`_refresh_prefix_this_step` 的判定条件是什么？论文要求"loss 在 **3 步**内不降 0.001 就重算"。
    - 当前 `loss_history` 上限是多少（2 还是 4）？
    - `loss_history[-4] - loss_history[-1] <= 0.001` 这种 3 步窗口是否实现？
    - 若只用了相邻 2 步差 → 记 ⚠️，给最小修复。
30. **缓存属性名**：`_clear_prefix_cache` 清空的是 `module.cached_prefixes`。请核对模型前向侧（`modeling_*.py` / `W8A16Model.forward`）在 `prefix=10` 时是否真的写入/读取同名属性。
    - 名字不一致 → `_clear_prefix_cache` 静默失效，前缀复用等于没实现 → 记 ❌ 并指出正确属性名。
    - 若模型侧完全没实现 prefix cache → 记 ❌（前缀复用只是传参，没有实际复用）。
31. **hardcoded 400 步**：之前版本有 `current_iteration >= 400` 强制关闭 prefix，论文无此逻辑。当前副本是否已删除？
32. **yaml 开关**：`use_random_prefix: true/false` 是否控制整个前缀复用分支（False 时走 `model(**input_tok)` 无 prefix）。

## 六、组合正确性（MobiEdit = 上述四者组合）
33. **执行路径**：给定 yaml（`quantize: true, use_zo: true, use_random_prefix: true`），`execute_rome → compute_v_zo → ZOTrainer.forward_grad_step → zero_order_loss` 调用链是否完整？
34. **量化 × 前缀**：`zero_order_loss` 里 `model(**input_tok, prefix=10)` 时，`model` 是 `W8A16Model` 包装后的实例。确认 `W8A16Model.forward` 接受并透传 `prefix` 参数（否则 prefix 复用与量化不能同时开）。
35. **量化 × ZO 扰动**：`δ ± εv` 注入到 `down_proj` 输出，该处是否保持 float（由 skip_modules 保证）？若被量化，`jvp` 可能被量化格子吃掉 → 记 ❌ 风险点。
36. **早停 × 量化**：早停的 `compute_edit_quality` 在量化模型上跑，评估是否一致（用同一个 `model` 实例）？
37. **`hparams.last_steps` 统计**：外层 `run_knowedit_*.py` 是否读取 `hparams.last_steps` 并写入日志（用于对齐论文"平均 397 步"）？

## 七、论文未覆盖但代码存在的部分（标注即可，不改）
38. 列出以下函数，标注"论文未使用 / 实验变体 / 调试残留"：
   `compute_v_randomprefix`、`compute_v_randomprefix_zo`、`compute_v_rank2`、`compute_v_delta_mlp`、`compute_v_eval`、`ZOTrainer.forward_grad_step_hessian / _zoadamu / _choosev / _para`、`ZOTrainer.loss_backward`、`ZOTrainer.zo_step`。
39. `rome_main.py` 里残留的 `print(f"delta_u: {delta_u}")` / `print(f"before w: {w}")` 等大 tensor 打印，标注"应删除或加 debug 开关"。

---

## 汇总输出
最后输出：

**(a) 机制对照表**

| 机制 | 论文要求 | 代码实现 | 判定 | 阻塞复现？ |
|---|---|---|---|---|
| ROME 基线 | ... | ... | ✅/⚠️/❌ | 是/否 |
| ZO 公式 (2) 的 1/N | ... | ... | ... | ... |
| ... | ... | ... | ... | ... |

**(b) 阻塞项清单**（❌ 项，按影响排序）

**(c) 最小可跑 yaml**（基于现有 `ROMEHyperParams` 字段，给出 `quantize / use_zo / use_random_prefix / use_eval / early_stop_*` 的正确组合）

**(d) 不需要装 bitsandbytes 的确认**：明确指出 `editor.py` 里是否存在 `load_in_8bit=True` 或 `BitsAndBytesConfig`，若有则给出删除行号。若没有，说明当前 traceback 的来源（可能是 `rome_main.py:14` 的 import 触发，或 `peft_egg` 下的 import 链）。

## 约束
- 只读检查，除非发现**明确 bug 且改动 < 10 行**，先报告再改。
- 不要贴超过 5 行的源码片段。
- 不要建议大重构；只给"改 yaml / 改 skip_modules / 改 loss_history 长度 / 删 print / 删 load_in_8bit"这类最小改动。
- 不需要跑任何实验；用静态阅读 + 已有日志（`stdout.log`）做证据。