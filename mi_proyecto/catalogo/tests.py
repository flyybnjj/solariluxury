from django.test import TestCase
from django.db.models import ProtectedError
from catalogo.models import Producto, PreOrden, Pedido

class Bug003ProductDeleteCascadeTest(TestCase):
    def setUp(self):
        self.producto = Producto.objects.create(
            nombre="Jordan 4 Retro Test",
            precio=350000,
            precio_usd=380.00
        )
        self.orden = PreOrden.objects.create(
            codigo_orden="SL-2026-TEST03",
            nombre_cliente="Comprador Jordan",
            email_cliente="jordan@test.com",
            direccion_entrega="Av. Vitacura 123",
            producto=self.producto,
            cantidad=1,
            precio_total=350000
        )

    def test_deleting_product_with_orders_raises_protected_error(self):
        """
        BUG-003: Al borrar un producto que tiene órdenes o pedidos,
        debe lanzar ProtectedError y no borrar las órdenes en cascada.
        """
        with self.assertRaises(ProtectedError):
            self.producto.delete()

        # Las órdenes deben seguir existiendo intactas
        self.assertTrue(PreOrden.objects.filter(id=self.orden.id).exists())
        self.assertTrue(Pedido.objects.filter(codigo_pedido=self.orden.codigo_orden).exists())


class Bug012PreOrdenPedidoSyncTest(TestCase):
    def setUp(self):
        from catalogo.models import Talla, ProductoTalla, Tracker
        self.producto = Producto.objects.create(nombre="Test Sync Jacket", precio=200000, precio_usd=210)
        self.talla = Talla.objects.create(nombre="L")
        self.pt = ProductoTalla.objects.create(producto=self.producto, talla=self.talla, stock=8)

    def test_preorden_and_pedido_bidirectional_sync_and_cancellation(self):
        """
        BUG-012: PreOrden y Pedido deben mantenerse siempre sincronizados:
        (a) Crear PreOrden crea Pedido y Tracker automáticamente.
        (b) Cancelar PreOrden actualiza Pedido a CANCELADA y restituye stock.
        (c) Modificar Pedido (ej. desde Admin) actualiza la PreOrden.
        (d) Cancelar desde Pedido cancela PreOrden y restituye stock.
        """
        from catalogo.models import Tracker
        # 1. Crear PreOrden
        orden = PreOrden.objects.create(
            codigo_orden="SL-2026-SYNC01",
            nombre_cliente="Cliente Sync",
            email_cliente="sync@test.com",
            direccion_entrega="Santiago",
            producto=self.producto,
            talla="L",
            cantidad=2,
            precio_total=400000,
            estado="CONFIRMADA",
            dhl_tracking="DHL-CL-SYNC999"
        )
        # Se descuentan 2 de stock manualmente simulando checkout
        self.pt.stock = 6
        self.pt.save()

        pedido = Pedido.objects.get(codigo_pedido="SL-2026-SYNC01")
        self.assertEqual(pedido.estado, "CONFIRMADA")
        self.assertEqual(pedido.precio_total, 400000)
        tracker = Tracker.objects.get(numero_guia="DHL-CL-SYNC999")
        self.assertEqual(tracker.pedido, pedido)

        # 2. Cancelar desde PreOrden restituye stock y actualiza Pedido
        orden.cancelar_y_restituir_stock()
        self.pt.refresh_from_db()
        self.assertEqual(self.pt.stock, 8)
        pedido.refresh_from_db()
        self.assertEqual(pedido.estado, "CANCELADA")

        # 3. Modificar desde Pedido (como haría Django Admin)
        pedido.estado = "DESPACHO_DHL"
        pedido.notas = "Despachado en valija diplomática"
        pedido.save()
        orden.refresh_from_db()
        self.assertEqual(orden.estado, "DESPACHO_DHL")
        self.assertEqual(orden.notas, "Despachado en valija diplomática")

        # 4. Cancelar directamente desde Pedido
        self.pt.stock = 6
        self.pt.save()
        res = pedido.cancelar_y_restituir_stock()
        self.assertTrue(res)
        self.pt.refresh_from_db()
        self.assertEqual(self.pt.stock, 8)
        orden.refresh_from_db()
        self.assertEqual(orden.estado, "CANCELADA")

