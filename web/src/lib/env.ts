import { z } from "zod";

const EnvSchema = z.object({
  DATABASE_URL: z.string().url().optional(),
  AUTH_ALLOWED_EMAILS: z.string().optional(),
  AUTH_SECRET: z.string().optional(),
});

export const env = EnvSchema.parse(process.env);
