CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE EXTENSION IF NOT EXISTS "vector";

CREATE TYPE "StepType" AS ENUM ('assistant_message', 'embedding', 'llm', 'retrieval', 'rerank', 'run', 'system_message', 'tool', 'undefined', 'user_message');

CREATE TYPE "MemoryStrategy" AS ENUM ('SEMANTIC', 'USER_PREFERENCE', 'SUMMARY');

CREATE TABLE IF NOT EXISTS "Element" (
    "id" TEXT NOT NULL DEFAULT gen_random_uuid(),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "threadId" TEXT,
    "stepId" TEXT NOT NULL,
    "metadata" JSONB NOT NULL,
    "mime" TEXT,
    "name" TEXT NOT NULL,
    "objectKey" TEXT,
    "url" TEXT,
    "chainlitKey" TEXT,
    "display" TEXT,
    "size" TEXT,
    "language" TEXT,
    "page" INTEGER,
    "props" JSONB,

    CONSTRAINT "Element_pkey" PRIMARY KEY ("id")
);

CREATE TABLE IF NOT EXISTS "User" (
    "id" TEXT NOT NULL DEFAULT gen_random_uuid(),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "metadata" JSONB NOT NULL,
    "identifier" TEXT NOT NULL,

    CONSTRAINT "User_pkey" PRIMARY KEY ("id")
);

CREATE TABLE IF NOT EXISTS "Feedback" (
    "id" TEXT NOT NULL DEFAULT gen_random_uuid(),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "stepId" TEXT,
    "name" TEXT NOT NULL,
    "value" DOUBLE PRECISION NOT NULL,
    "comment" TEXT,

    CONSTRAINT "Feedback_pkey" PRIMARY KEY ("id")
);

CREATE TABLE IF NOT EXISTS "Step" (
    "id" TEXT NOT NULL DEFAULT gen_random_uuid(),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "parentId" TEXT,
    "threadId" TEXT,
    "input" TEXT,
    "metadata" JSONB NOT NULL,
    "name" TEXT,
    "output" TEXT,
    "type" "StepType" NOT NULL,
    "showInput" TEXT DEFAULT 'json',
    "isError" BOOLEAN DEFAULT false,
    "startTime" TIMESTAMP(3) NOT NULL,
    "endTime" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "Step_pkey" PRIMARY KEY ("id")
);

CREATE TABLE IF NOT EXISTS "Thread" (
    "id" TEXT NOT NULL DEFAULT gen_random_uuid(),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "deletedAt" TIMESTAMP(3),
    "name" TEXT,
    "metadata" JSONB NOT NULL,
    "userId" TEXT,

    CONSTRAINT "Thread_pkey" PRIMARY KEY ("id")
);

CREATE TABLE IF NOT EXISTS "ThreadMemory" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "userId" VARCHAR(255),
    "threadId" VARCHAR(255),
    "strategy" "MemoryStrategy" NOT NULL,
    "namespace" TEXT,
    "embedding" VECTOR(3072),
    "content" TEXT NOT NULL,
    "metadata" JSONB,
    "createdAt" TIMESTAMP DEFAULT NOW(),
    "updatedAt" TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY ("userId") REFERENCES "User"("id")
);

CREATE TABLE "ExchangeThread" (
    "id" VARCHAR(36) PRIMARY KEY,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE "ExchangeMessage" (
    "id" INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    "thread_id" VARCHAR(36) NOT NULL,
    "role" VARCHAR(20) NOT NULL,
    "content" TEXT NOT NULL,
    "is_summarized" BOOLEAN NOT NULL DEFAULT FALSE,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS "Element_stepId_idx" ON "Element"("stepId");

CREATE INDEX IF NOT EXISTS "Element_threadId_idx" ON "Element"("threadId");

CREATE INDEX IF NOT EXISTS "User_identifier_idx" ON "User"("identifier");

CREATE UNIQUE INDEX IF NOT EXISTS "User_identifier_key" ON "User"("identifier");

CREATE INDEX IF NOT EXISTS "Feedback_createdAt_idx" ON "Feedback"("createdAt");

CREATE INDEX IF NOT EXISTS "Feedback_name_idx" ON "Feedback"("name");

CREATE INDEX IF NOT EXISTS "Feedback_stepId_idx" ON "Feedback"("stepId");

CREATE INDEX IF NOT EXISTS "Feedback_value_idx" ON "Feedback"("value");

CREATE INDEX IF NOT EXISTS "Feedback_name_value_idx" ON "Feedback"("name", "value");

CREATE INDEX IF NOT EXISTS "Step_createdAt_idx" ON "Step"("createdAt");

CREATE INDEX IF NOT EXISTS "Step_endTime_idx" ON "Step"("endTime");

CREATE INDEX IF NOT EXISTS "Step_parentId_idx" ON "Step"("parentId");

CREATE INDEX IF NOT EXISTS "Step_startTime_idx" ON "Step"("startTime");

CREATE INDEX IF NOT EXISTS "Step_threadId_idx" ON "Step"("threadId");

CREATE INDEX IF NOT EXISTS "Step_type_idx" ON "Step"("type");

CREATE INDEX IF NOT EXISTS "Step_name_idx" ON "Step"("name");

CREATE INDEX IF NOT EXISTS "Step_threadId_startTime_endTime_idx" ON "Step"("threadId", "startTime", "endTime");

CREATE INDEX IF NOT EXISTS "Thread_createdAt_idx" ON "Thread"("createdAt");

CREATE INDEX IF NOT EXISTS "Thread_name_idx" ON "Thread"("name");

CREATE INDEX IF NOT EXISTS idx_strategy ON "ThreadMemory"("strategy");

CREATE INDEX IF NOT EXISTS idx_userId ON "ThreadMemory"("userId");

CREATE INDEX IF NOT EXISTS idx_threadId ON "ThreadMemory"("threadId");

CREATE INDEX IF NOT EXISTS idx_namespace ON "ThreadMemory"("namespace");

CREATE INDEX IF NOT EXISTS idx_exchange_message_thread_id ON "ExchangeMessage" ("thread_id");

CREATE INDEX IF NOT EXISTS idx_threadmemory_embedding ON "ThreadMemory" USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

ALTER TABLE "Element" ADD CONSTRAINT "Element_stepId_fkey" FOREIGN KEY ("stepId") REFERENCES "Step"("id") ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE "Element" ADD CONSTRAINT "Element_threadId_fkey" FOREIGN KEY ("threadId") REFERENCES "Thread"("id") ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE "Feedback" ADD CONSTRAINT "Feedback_stepId_fkey" FOREIGN KEY ("stepId") REFERENCES "Step"("id") ON DELETE SET NULL ON UPDATE CASCADE;

ALTER TABLE "Step" ADD CONSTRAINT "Step_parentId_fkey" FOREIGN KEY ("parentId") REFERENCES "Step"("id") ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE "Step" ADD CONSTRAINT "Step_threadId_fkey" FOREIGN KEY ("threadId") REFERENCES "Thread"("id") ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE "Thread" ADD CONSTRAINT "Thread_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE SET NULL ON UPDATE CASCADE;

ALTER TABLE "ExchangeMessage" ADD CONSTRAINT "fk_exchange_message_thread" FOREIGN KEY ("thread_id") REFERENCES "ExchangeThread" ("id") ON DELETE CASCADE;
