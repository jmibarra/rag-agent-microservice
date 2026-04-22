import sys
import os

# Add the project root to sys.path to allow imports from 'app'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.jira_service import jira_service

def test_incident_flow_mock():
    """
    This script tests the incident creation flow in MOCK MODE.
    IT DOES NOT CREATE ANY TICKETS IN JIRA.
    """
    print("=== TESTING INCIDENT FLOW (MOCK MODE) ===")
    
    # Sample data that the agent would collect
    summary = "SISTEMA INTEGRAL DE SOPORTE - TEST"
    description = "Prueba de flujo de creación de incidente con nuevos campos custom."
    producto_id = "10026" # Agilis - AMS
    proceso_afectado_id = "10042" # No afecta ningún proceso clave
    afectacion_id = "10050" # Imperceptible
    
    print(f"Campos a enviar:")
    print(f"  - Summary: {summary}")
    print(f"  - Description: {description}")
    print(f"  - Producto ID: {producto_id}")
    print(f"  - Proceso ID: {proceso_afectado_id}")
    print(f"  - Afectación ID: {afectacion_id}")
    print("-" * 40)
    
    # Call the service (which is currently mocked/protected in jira_service.py)
    result = jira_service.create_customer_request(
        summary=summary,
        description=description,
        producto_id=producto_id,
        proceso_afectado_id=proceso_afectado_id,
        afectacion_id=afectacion_id
    )
    
    print(f"\nResultado recibido del servicio:\n{result}")
    print("=" * 40)
    print("AVISO: Si ves el mensaje de 'SIMULACIÓN', significa que el código de seguridad está activo y NO se creó nada en el Jira real.")

if __name__ == "__main__":
    test_incident_flow_mock()
