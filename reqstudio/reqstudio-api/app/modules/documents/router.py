"""Documents router — upload, listagem, remoção (Stories 4.1 + 4.2).

Endpoints:
  POST   /api/v1/projects/{project_id}/documents           → upload multipart
  GET    /api/v1/projects/{project_id}/documents           → lista docs
  DELETE /api/v1/projects/{project_id}/documents/{doc_id} → remove doc + chunks
"""

from fastapi import APIRouter, Depends, File, UploadFile, status

from app.db.tenant import TenantScope, get_tenant_scope
from app.modules.documents import service
from app.modules.documents.schemas import DocumentListResponse, DocumentResponse
from app.schemas.response import ApiResponse

router = APIRouter(
    prefix="/projects/{project_id}/documents",
    tags=["documents"],
)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=ApiResponse[DocumentResponse],
    summary="Upload de documento de referência (PDF ou Markdown)",
)
async def upload_document(
    project_id: str,
    file: UploadFile = File(...),
    scope: TenantScope = Depends(get_tenant_scope),
) -> ApiResponse[DocumentResponse]:
    content = await file.read()
    doc = await service.upload_document(
        scope=scope,
        project_id=project_id,
        filename=file.filename or "document",
        content=content,
    )
    return ApiResponse(data=doc)


@router.get(
    "",
    response_model=ApiResponse[DocumentListResponse],
    summary="Listar documentos do projeto",
)
async def list_documents(
    project_id: str,
    scope: TenantScope = Depends(get_tenant_scope),
) -> ApiResponse[DocumentListResponse]:
    result = await service.list_documents(scope=scope, project_id=project_id)
    return ApiResponse(data=result)


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover documento e seus chunks",
)
async def delete_document(
    project_id: str,
    document_id: str,
    scope: TenantScope = Depends(get_tenant_scope),
) -> None:
    await service.delete_document(
        scope=scope,
        project_id=project_id,
        document_id=document_id,
    )
