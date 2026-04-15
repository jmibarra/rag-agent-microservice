import os
import sys

# Agregar el directorio raíz al path para poder importar módulos de 'app'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.jira_service import jira_service


def test_get_customer_by_phone():
    telefono_prueba = "1156570822"  # Puedes reemplazarlo por el valor real a buscar
    campo_busqueda = "Teléfono asociado"

    print(f"=== Probando obtener cliente de Jira Service Management ===")
    print(f"Campo: '{campo_busqueda}' | Valor: '{telefono_prueba}'\n")

    resultado = jira_service.get_customer_by_detail_field(
        campo_busqueda, telefono_prueba
    )

    if resultado:
        print("✅ Resultado obtenido exitosamente:")
        # Imprime la respuesta JSON formateada para leerla mejor
        import json

        customer_json = json.dumps(resultado, indent=4, ensure_ascii=False)
        print(customer_json)

        customer_details = jira_service.get_customer_by_id(
            resultado.get("customers", [])[0].get("id")
        )

        if customer_details:
            print("✅ Cliente obtenido exitosamente:")
            print(json.dumps(customer_details, indent=4, ensure_ascii=False))
        else:
            print(
                "❌ No se obtuvo un cliente o hubo un error (verifica los logs arriba)."
            )
    else:
        print("❌ No se obtuvo un cliente o hubo un error (verifica los logs arriba).")


if __name__ == "__main__":
    test_get_customer_by_phone()
