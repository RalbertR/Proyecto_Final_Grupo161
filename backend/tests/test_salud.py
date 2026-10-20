def test_salud_responde_ok_con_la_base_conectada(client):
    respuesta = client.get("/api/salud")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"estado": "ok"}
