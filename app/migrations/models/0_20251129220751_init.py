from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "fileanchor" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "name" VARCHAR(255) NOT NULL,
    "path" VARCHAR(1024) NOT NULL,
    "description" TEXT,
    "create_time" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "update_time" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "is_valid" INT NOT NULL DEFAULT 1
) /* 资料文件锚点 */;
CREATE TABLE IF NOT EXISTS "backuprecord" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "backup_path" VARCHAR(1024) NOT NULL,
    "backup_time" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "file_anchor_id" INT NOT NULL REFERENCES "fileanchor" ("id") ON DELETE CASCADE
) /* 资料备份记录 */;
CREATE TABLE IF NOT EXISTS "operatortype" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "name" VARCHAR(100) NOT NULL UNIQUE,
    "description" TEXT
) /* 操作类型 */;
CREATE TABLE IF NOT EXISTS "operatorlog" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "result" TEXT NOT NULL,
    "time" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "operator_type_id" INT NOT NULL REFERENCES "operatortype" ("id") ON DELETE CASCADE
) /* 操作日志 */;
CREATE TABLE IF NOT EXISTS "tag" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "name" VARCHAR(100) NOT NULL UNIQUE,
    "use_count" INT NOT NULL DEFAULT 0,
    "create_time" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) /* 资料标签 */;
CREATE TABLE IF NOT EXISTS "virtualfold" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "name" VARCHAR(255) NOT NULL UNIQUE,
    "description" TEXT,
    "create_time" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) /* 虚拟文件夹 */;
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSON NOT NULL
);
CREATE TABLE IF NOT EXISTS "fileanchor_virtualfold" (
    "fileanchor_id" INT NOT NULL REFERENCES "fileanchor" ("id") ON DELETE CASCADE,
    "virtualfold_id" INT NOT NULL REFERENCES "virtualfold" ("id") ON DELETE CASCADE
);
CREATE UNIQUE INDEX IF NOT EXISTS "uidx_fileanchor__fileanc_e82e0a" ON "fileanchor_virtualfold" ("fileanchor_id", "virtualfold_id");
CREATE TABLE IF NOT EXISTS "fileanchor_tag" (
    "fileanchor_id" INT NOT NULL REFERENCES "fileanchor" ("id") ON DELETE CASCADE,
    "tag_id" INT NOT NULL REFERENCES "tag" ("id") ON DELETE CASCADE
);
CREATE UNIQUE INDEX IF NOT EXISTS "uidx_fileanchor__fileanc_ddd7e0" ON "fileanchor_tag" ("fileanchor_id", "tag_id");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "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"
)
