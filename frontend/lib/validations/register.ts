import { z } from 'zod';

// ──────────────────────────────────────────────────────────────────────────
// STEP 1 — ACCOUNT
// ──────────────────────────────────────────────────────────────────────────

export const step1Schema = z
  .object({
    firstName: z.string().min(2, 'Minimum 2 caractères'),
    lastName: z.string().min(2, 'Minimum 2 caractères'),
    email: z
      .string()
      .email('Email invalide'),
    password: z
      .string()
      .min(12, '12 caractères minimum')
      .regex(/[A-Z]/, 'Une majuscule requise')
      .regex(/[0-9]/, 'Un chiffre requis')
      .regex(/[^A-Za-z0-9]/, 'Un caractère spécial requis'),
    confirmPassword: z.string(),
    acceptTerms: z.boolean().refine((v) => v === true, 'Obligatoire'),
  })
  .refine((d: any) => d.password === d.confirmPassword, {
    message: 'Les mots de passe ne correspondent pas',
    path: ['confirmPassword'],
  });

export type Step1Data = z.infer<typeof step1Schema>;

// ──────────────────────────────────────────────────────────────────────────
// STEP 2 — ORGANIZATION
// ──────────────────────────────────────────────────────────────────────────

export const step2Schema = z.object({
  orgName: z.string().min(2, 'Nom requis'),
  sector: z.string().min(1, 'Secteur requis'),
  country: z.string().min(1, 'Pays requis'),
  orgSize: z.enum(['1-10', '11-50', '51-200', '201-500', '500+'], {
    message: 'Taille requise',
  }),
  portals: z
    .array(z.string())
    .min(1, 'Sélectionner au moins un portail'),
});

export type Step2Data = z.infer<typeof step2Schema>;

// ──────────────────────────────────────────────────────────────────────────
// STEP 3 — PLAN
// ──────────────────────────────────────────────────────────────────────────

export const step3Schema = z.object({
  plan: z.enum(['fondements', 'avancee', 'entreprise'], {
    message: 'Formule requise',
  }),
  billing: z
    .enum(['monthly', 'annual'], {
      message: 'Facturation requise',
    }),
});

export type Step3Data = z.infer<typeof step3Schema>;

// ──────────────────────────────────────────────────────────────────────────
// FULL REGISTRATION SCHEMA (combined)
// ──────────────────────────────────────────────────────────────────────────

export const registerSchema = step1Schema
  .merge(step2Schema)
  .merge(step3Schema);

export type RegisterFormData = z.infer<typeof registerSchema>;
