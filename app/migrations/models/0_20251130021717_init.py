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
CREATE TABLE IF NOT EXISTS "virtualfolder" (
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
CREATE TABLE IF NOT EXISTS "fileanchor_virtualfolder" (
    "fileanchor_id" INT NOT NULL REFERENCES "fileanchor" ("id") ON DELETE CASCADE,
    "virtualfolder_id" INT NOT NULL REFERENCES "virtualfolder" ("id") ON DELETE CASCADE
);
CREATE UNIQUE INDEX IF NOT EXISTS "uidx_fileanchor__fileanc_58d806" ON "fileanchor_virtualfolder" ("fileanchor_id", "virtualfolder_id");
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
