# 架构修复_SwaggerUI路径修复与v1.2.2发版

标签: #架构 #FastAPI #SwaggerUI #版本号 #docs_url

- 适用任务: 待补充
- 引用规则:
  - ai_rules/README.md v0.1
  - ai_rules/task_rules/basic_rules.md v0.1
  - ai_rules/memory_rules/basic_rules.md v0.1

## 最短路径
1. 阅读 ai_rules/README.md 及各扩展规则
2. 阅读 doc/tbp_v1.1.md 确认职责
3. 阅读 backend/src/air_memory/main.py 确认 FastAPI 构造参数
4. 在 FastAPI() 构造中添加 docs_url='/api/v1/docs', redoc_url='/api/v1/redoc', openapi_url='/api/v1/openapi.json'
5. 将 APP_VERSION 升级至 1.2.2
6. 同步更新 backend/pyproject.toml version = '1.2.2'
7. 同步更新 start.bat 版本号字符串 v1.2.2
8. 同步更新 start.sh 版本号字符串 v1.2.2
9. git add 上述 4 个文件并 git commit
10. 使用 parallel_validation 验证变更
11. 汇报结果给 Nia
