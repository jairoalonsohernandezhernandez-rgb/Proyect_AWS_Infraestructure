# Arquitectura Serverless de Ingesta de Eventos en AWS

Arquitectura serverless en AWS que desacopla la recepción de eventos del procesamiento, usando **API Gateway → SQS → Lambda → S3**, con la infraestructura completamente definida en Terraform y desplegada mediante un pipeline de CI/CD autenticado con **OIDC** (sin credenciales estáticas).

## Arquitectura

```
Cliente ──▶ API Gateway ──▶ SQS (buffer) ──▶ Lambda ──▶ S3
                                                          │
                                                 Lifecycle policy:
                                                 Standard → Standard-IA (30d)
                                                 → Glacier (90d) → Eliminación (365d)
```

1. **API Gateway** recibe la petición del cliente y publica el evento en una cola **SQS**.
2. **SQS** actúa como buffer: desacopla la recepción del procesamiento, controla el ritmo al que Lambda recibe trabajo ante picos de tráfico, y garantiza que ningún evento se pierda si el consumidor falla momentáneamente.
3. **Lambda** consume los mensajes de la cola de forma asíncrona, escalando automáticamente según el volumen disponible. El handler (`index.js`):
   - Extrae el cuerpo del mensaje recibido desde SQS.
   - Parsea el contenido, contemplando el formato codificado por API Gateway.
   - Genera una clave única para el objeto.
   - Sube el evento procesado a S3.
4. **S3** almacena los eventos procesados, con una política de **lifecycle** que gestiona el costo de almacenamiento a lo largo del tiempo.

## ¿Por qué SQS entre API Gateway y Lambda?

No es un balanceador de carga — Lambda ya escala automáticamente sin necesidad de SQS. La cola cumple dos funciones distintas:

- **Control de tráfico**: amortigua picos de peticiones, evitando que un volumen alto sature recursos aguas abajo.
- **Durabilidad**: si Lambda falla o está momentáneamente ocupada, el mensaje permanece en la cola y se reintenta, en vez de perderse.

## Seguridad e IAM

El pipeline se autentica con AWS mediante **OIDC** (OpenID Connect), sin almacenar credenciales de larga duración como secretos en GitHub.

Cada componente opera con un **rol de IAM independiente y de permisos mínimos**, según su función:

| Rol | Permisos |
|---|---|
| **API Gateway** | `sqs:SendMessage` — solo puede publicar en la cola |
| **Lambda** | `sqs:ReceiveMessage`, `sqs:DeleteMessage`, `sqs:GetQueueAttributes` sobre SQS · `s3:PutObject`, `s3:GetObject` sobre S3 |

Ningún rol tiene permisos fuera de lo que su función requiere (API Gateway no puede leer ni borrar de la cola; Lambda no tiene permisos sobre API Gateway).

## Gestión de costos — Lifecycle del bucket S3

| Período | Clase de almacenamiento |
|---|---|
| 0 – 30 días | S3 Standard |
| 30 – 90 días | S3 Standard-IA |
| 90 – 365 días | S3 Glacier |
| 365 días | Eliminación automática |

Esto reduce el costo de almacenamiento de eventos antiguos sin intervención manual.

## Pipeline de CI/CD (GitHub Actions)

El workflow se ejecuta en cada push y pull request a `main`:

1. Checkout del código.
2. Autenticación con AWS vía OIDC (`aws-actions/configure-aws-credentials`).
3. Setup de Terraform.
4. `terraform fmt -check` — valida el formato del código.
5. `terraform plan` — en pull requests, se queda aquí (solo revisión, sin aplicar cambios).
6. `terraform apply` — solo se ejecuta en push directo a `main`.

## Estructura del repositorio

```
.
├── .github/workflows/        # Pipeline de CI/CD
├── terraform/environments/dev/   # Infraestructura como código
└── (Lambda) index.js         # Handler de procesamiento
```

## Tecnologías

Terraform · AWS (API Gateway, SQS, Lambda, S3, IAM, STS) · GitHub Actions · OIDC · Node.js

---

*Proyecto personal de práctica, orientado a arquitectura de soluciones serverless y buenas prácticas de seguridad en pipelines CI/CD.*
