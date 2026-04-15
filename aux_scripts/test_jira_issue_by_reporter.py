import os
import sys

# Agregar el directorio raíz al path para poder importar módulos de 'app'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.jira_service import jira_service


def test_get_issue_by_reporter():
    issue_key = "SOP-10336"

    customer = jira_service.get_customer_by_detail_field(
        "Teléfono asociado", "1156570822"
    )

    customer_context = customer.get("customers", [])[0]
    print(customer_context)

    issue = jira_service.get_issue_details_filtered(issue_key, customer_context)

    print(issue)

    # if not customer:
    #     print("No se obtuvo un cliente o hubo un error (verifica los logs arriba).")
    #     return None

    # customer_id = customer.get("customers", [])[0].get("id")

    # customer_data = jira_service.get_customer_by_id(customer_id)

    # if not customer_data:
    #     print("No se obtuvo un cliente o hubo un error (verifica los logs arriba).")
    #     return None

    # organizations = customer_data.get("organizations", [])
    # organization = ""
    # if len(organizations) == 0:
    #     print("No se obtuvo una organización.")
    # else:
    #     organization = organizations[0].get("name")

    # print(f"Organization: {organization}")

    # print(f"=== Probando obtener ticket de Jira Service Management ===")
    # print(f"Issue: '{issue_key}' | Reporter: '{reporter}'\n")

    # resultado = jira_service.get_issue_details_by_reporter_or_rp_or_organization(
    #     issue_key, reporter, customer_id, organization
    # )

    # last_comment = jira_service.get_last_public_comment_by_key(issue_key)

    # print(last_comment)

    # if resultado:
    #     print("✅ Resultado obtenido exitosamente:")
    #     print(resultado)
    # else:
    #     print(
    #         f"❌ No se obtuvo un ticket para {issue_key} customer {customer_data.get('name')} o hubo un error (verifica los logs arriba)."
    #     )


if __name__ == "__main__":
    test_get_issue_by_reporter()
