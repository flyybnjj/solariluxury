import json
from unittest.mock import patch
from django.test import TestCase, Client, override_settings
from django.core import mail
from catalogo.models import Producto, Talla, ProductoTalla, PreOrden

@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class Bug001PriceSpoofingTest(TestCase):
    def setUp(self):
        self.client = Client()
        from django.contrib.auth.models import User
        self.user = User.objects.create_user(username='price-check', email='price-check@example.test', password='StrongPassphrase-2026!')
        self.client.force_login(self.user)
        self.producto = Producto.objects.create(
            nombre="Gorra Syna Test",
            precio=222000,
            precio_usd=230.00
        )

    def test_cart_price_spoofing_prevented(self):
        """
        BUG-001: El atacante envía 'price': '$1 CLP' para 2 items de $222.000.
        El backend NO debe cobrar $2 CLP. Debe calcular sobre Producto.precio ($444.000).
        """
        payload = {
            "nombre_cliente": "Hacker Price",
            "email_cliente": "hacker@test.com",
            "direccion_entrega": "Calle Falsa 123",
            "items": [
                {"id": self.producto.id, "name": "Fake Price 1", "price": "$1 CLP", "quantity": 1, "size": "M"},
                {"id": self.producto.id, "name": "Fake Price 2", "price": "$1 CLP", "quantity": 1, "size": "M"}
            ]
        }
        response = self.client.post(
            '/api/crear-preorden/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))

        orden = PreOrden.objects.get(codigo_orden=data['codigo_orden'])
        self.assertEqual(orden.precio_total, self.producto.precio * 2)
        self.assertEqual(orden.usuario, self.user)
        self.assertEqual(orden.email_cliente, self.user.email)

    def test_invalid_product_id_returns_400(self):
        payload = {
            "nombre_cliente": "Hacker ID",
            "email_cliente": "hacker@test.com",
            "direccion_entrega": "Calle Falsa 123",
            "items": [
                {"id": 999999, "quantity": 1}
            ]
        }
        response = self.client.post(
            '/api/crear-preorden/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data.get('success'))

    def test_invalid_quantity_returns_400(self):
        payload = {
            "nombre_cliente": "Hacker Cantidad",
            "email_cliente": "hacker@test.com",
            "direccion_entrega": "Calle Falsa 123",
            "items": [
                {"id": self.producto.id, "quantity": -5}
            ]
        }
        response = self.client.post(
            '/api/crear-preorden/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data.get('success'))


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class Bug004StockDeductionTest(TestCase):
    def setUp(self):
        self.client = Client()
        from django.contrib.auth.models import User
        self.user = User.objects.create_user(username='stock-buyer', email='stock-buyer@example.test', password='StrongPassphrase-2026!')
        self.client.force_login(self.user)
        self.producto = Producto.objects.create(
            nombre="Jordan 4 Military Black",
            precio=290000,
            precio_usd=310.00
        )
        self.talla_m = Talla.objects.create(nombre="M")
        self.pt = ProductoTalla.objects.create(
            producto=self.producto,
            talla=self.talla_m,
            stock=5
        )

    def test_stock_deducted_after_successful_purchase(self):
        """(a) stock 5, compra 1, queda 4"""
        payload = {
            "nombre_cliente": "Buyer 1",
            "email_cliente": "buyer1@test.com",
            "direccion_entrega": "Santiago",
            "producto_id": self.producto.id,
            "talla": "M",
            "cantidad": 1
        }
        response = self.client.post('/api/crear-preorden/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.pt.refresh_from_db()
        self.assertEqual(self.pt.stock, 4)

    def test_purchase_rejected_if_quantity_exceeds_stock(self):
        """(b) stock 1, compra 2, se rechaza y queda 1"""
        self.pt.stock = 1
        self.pt.save()

        payload = {
            "nombre_cliente": "Buyer Over",
            "email_cliente": "buyerover@test.com",
            "direccion_entrega": "Santiago",
            "producto_id": self.producto.id,
            "talla": "M",
            "cantidad": 2
        }
        response = self.client.post('/api/crear-preorden/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.pt.refresh_from_db()
        self.assertEqual(self.pt.stock, 1)

    def test_purchase_rejected_if_stock_is_zero(self):
        """(c) stock 0, se rechaza"""
        self.pt.stock = 0
        self.pt.save()

        payload = {
            "nombre_cliente": "Buyer Zero",
            "email_cliente": "zero@test.com",
            "direccion_entrega": "Santiago",
            "producto_id": self.producto.id,
            "talla": "M",
            "cantidad": 1
        }
        response = self.client.post('/api/crear-preorden/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.pt.refresh_from_db()
        self.assertEqual(self.pt.stock, 0)

    def test_consecutive_purchases_exhaust_stock_cleanly(self):
        """(d) dos compras consecutivas del último ítem, solo una pasa"""
        self.pt.stock = 1
        self.pt.save()

        payload = {
            "nombre_cliente": "Buyer Fast 1",
            "email_cliente": "fast1@test.com",
            "direccion_entrega": "Santiago",
            "producto_id": self.producto.id,
            "talla": "M",
            "cantidad": 1
        }
        resp1 = self.client.post('/api/crear-preorden/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(resp1.status_code, 200)

        # Segunda compra debe ser rechazada
        payload["email_cliente"] = "fast2@test.com"
        resp2 = self.client.post('/api/crear-preorden/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(resp2.status_code, 400)
        self.pt.refresh_from_db()
        self.assertEqual(self.pt.stock, 0)

    def test_stock_rollback_if_order_creation_fails(self):
        """(e) si falla la orden a mitad de camino, el stock hace rollback"""
        self.pt.stock = 5
        self.pt.save()

        payload = {
            "nombre_cliente": "Buyer Fail",
            "email_cliente": "fail@test.com",
            "direccion_entrega": "Santiago",
            "producto_id": self.producto.id,
            "talla": "M",
            "cantidad": 1
        }
        with patch('catalogo.models.PreOrden.objects.create', side_effect=RuntimeError("Database failure")):
            response = self.client.post('/api/crear-preorden/', data=json.dumps(payload), content_type='application/json')
            self.assertEqual(response.status_code, 500)

        self.pt.refresh_from_db()
        self.assertEqual(self.pt.stock, 5)

    def test_order_cancellation_restores_stock(self):
        """Si la orden se cancela, el stock reservado debe restituirse a la base de datos."""
        payload = {
            "nombre_cliente": "Buyer Cancel",
            "email_cliente": "cancel@test.com",
            "direccion_entrega": "Santiago",
            "producto_id": self.producto.id,
            "talla": "M",
            "cantidad": 2
        }
        resp = self.client.post('/api/crear-preorden/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.pt.refresh_from_db()
        self.assertEqual(self.pt.stock, 3)

        orden = PreOrden.objects.get(codigo_orden=resp.json()['codigo_orden'])
        orden.cancelar_y_restituir_stock()
        self.pt.refresh_from_db()
        self.assertEqual(self.pt.stock, 5)


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class Bug016EmailProductMismatchTest(TestCase):
    def test_email_renders_real_product_not_hardcoded_af1(self):
        """
        BUG-016: El correo debe renderizar el producto, imagen y código real
        de lo que el cliente compró, nunca los valores hardcodeados de la AF1.
        """
        productos_prueba = [
            Producto.objects.create(nombre="New Era Syna World 59FIFTY Hat", precio=222000, precio_usd=230, imagen="img/hat.jpg"),
            Producto.objects.create(nombre="Trapstar Chenille Tracksuit Black", precio=310000, precio_usd=330, imagen="img/tracksuit.jpg"),
            Producto.objects.create(nombre="Audemars Piguet Royal Pop Ocho", precio=1048000, precio_usd=1100, imagen="img/watch.jpg")
        ]

        from locales.views import enviar_correo_preorden

        for prod in productos_prueba:
            orden = PreOrden.objects.create(
                codigo_orden=f"SL-2026-T{prod.id}",
                nombre_cliente="Cliente Real",
                email_cliente="real_buyer@test.com",
                direccion_entrega="Av. del Mar 400",
                ciudad="La Serena",
                producto=prod,
                talla="L",
                cantidad=1,
                precio_total=prod.precio,
                estado="CONFIRMADA",
                dhl_tracking="DHL-CL-12345678"
            )
            enviar_correo_preorden(orden)
            self.assertGreater(len(mail.outbox), 0)
            ultimo_correo = mail.outbox[-1]
            cuerpo_html = ultimo_correo.alternatives[0][0]

            # 1. Debe contener el nombre real del producto comprado
            self.assertIn(prod.nombre, cuerpo_html)

            # 2. NO debe contener los valores fijos hardcodeados de la AF1
            self.assertNotIn("Nike Air Force 1", cuerpo_html)
            self.assertNotIn("FZ4210-001", cuerpo_html)
            self.assertNotIn("af1_syna_email.png", cuerpo_html)
            self.assertNotIn("$189.990", cuerpo_html)


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class Bug005CartItemsTest(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        self.user = User.objects.create_user(username='cart-buyer', email='cart-buyer@example.test', password='StrongPassphrase-2026!')
        self.client.force_login(self.user)
        self.p1 = Producto.objects.create(nombre="Trapstar Hoodie", precio=120000, precio_usd=130)
        self.p2 = Producto.objects.create(nombre="Syna Cap", precio=45000, precio_usd=50)
        self.talla_m = Talla.objects.create(nombre="M")
        self.talla_l = Talla.objects.create(nombre="L")
        self.pt1 = ProductoTalla.objects.create(producto=self.p1, talla=self.talla_m, stock=10)
        self.pt2 = ProductoTalla.objects.create(producto=self.p2, talla=self.talla_l, stock=5)

    def test_single_item_in_cart_list_succeeds(self):
        """BUG-005: Carrito con un único item en la lista 'items' debe procesar correctamente."""
        payload = {
            "nombre": "Comprador Carrito Uno",
            "email": "single@test.com",
            "direccion": "Calle Central 100",
            "ciudad": "La Serena",
            "items": [
                {"id": self.p1.id, "quantity": 1, "size": "M"}
            ]
        }
        resp = self.client.post('/api/crear-preorden/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['success'])
        self.pt1.refresh_from_db()
        self.assertEqual(self.pt1.stock, 9)
        orden = PreOrden.objects.get(codigo_orden=data['codigo_orden'])
        self.assertEqual(orden.precio_total, 120000)
        self.assertEqual(orden.cantidad, 1)

    def test_multiple_items_in_cart_succeeds_and_deducts_all(self):
        """BUG-005: Carrito con múltiples items procesa y descuenta stock de cada uno."""
        payload = {
            "nombre": "Comprador Multi",
            "email": "multi@test.com",
            "direccion": "Av. Costanera 500",
            "items": [
                {"id": self.p1.id, "quantity": 2, "size": "M"},
                {"id": self.p2.id, "quantity": 3, "size": "L"}
            ]
        }
        resp = self.client.post('/api/crear-preorden/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.pt1.refresh_from_db()
        self.pt2.refresh_from_db()
        self.assertEqual(self.pt1.stock, 8)
        self.assertEqual(self.pt2.stock, 2)
        orden = PreOrden.objects.get(codigo_orden=resp.json()['codigo_orden'])
        self.assertEqual(orden.precio_total, (120000 * 2) + (45000 * 3))
        self.assertEqual(orden.cantidad, 5)

    def test_empty_cart_items_list_returns_400_empty_cart_error(self):
        """BUG-005: Carrito con items=[] explícito debe retornar 400 indicando carrito vacío."""
        payload = {
            "nombre": "Carrito Vacío",
            "email": "vacio@test.com",
            "items": []
        }
        resp = self.client.post('/api/crear-preorden/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("vacío", resp.json().get('error', '').lower())


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class Bug006CouponSecurityTest(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        from usuarios.models import Cliente
        self.user_a = User.objects.create_user(username="usera", email="usera@solary.cl", password="Password123!")
        self.cliente_a = self.user_a.cliente
        self.cliente_a.cupon_bienvenida_codigo = "SOLARY-USERA-15"
        self.cliente_a.save()

        self.user_b = User.objects.create_user(username="userb", email="userb@solary.cl", password="Password123!")
        self.cliente_b = self.user_b.cliente
        self.cliente_b.cupon_bienvenida_codigo = "SOLARY-USERB-15"
        self.cliente_b.save()

        self.producto = Producto.objects.create(nombre="Luxury Bag", precio=100000, precio_usd=100)
        self.talla = Talla.objects.create(nombre="M")
        self.pt = ProductoTalla.objects.create(producto=self.producto, talla=self.talla, stock=20)

    def test_valid_coupon_applies_discount_and_marks_used(self):
        """BUG-006: Un cupón válido aplica 15% de descuento y queda marcado como usado."""
        self.client.force_login(self.user_a)
        payload = {
            "nombre": "User A",
            "email": self.user_a.email,
            "producto_id": self.producto.id,
            "talla": "M",
            "cantidad": 1,
            "cupon": "SOLARY-USERA-15"
        }
        resp = self.client.post('/api/crear-preorden/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        orden = PreOrden.objects.get(codigo_orden=resp.json()['codigo_orden'])
        # 100.000 - 15% = 85.000
        self.assertEqual(orden.precio_total, 85000)
        self.cliente_a.refresh_from_db()
        self.assertTrue(getattr(self.cliente_a, 'cupon_usado', False))

    def test_reusing_used_coupon_is_rejected(self):
        """BUG-006: Reutilizar un cupón ya consumido debe ser rechazado con 400."""
        self.cliente_a.cupon_usado = True
        self.cliente_a.save()
        self.client.force_login(self.user_a)
        payload = {
            "nombre": "User A",
            "email": self.user_a.email,
            "producto_id": self.producto.id,
            "talla": "M",
            "cantidad": 1,
            "cupon": "SOLARY-USERA-15"
        }
        resp = self.client.post('/api/crear-preorden/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(resp.status_code, 400)
        err = resp.json().get('error', '').lower()
        self.assertTrue('utilizado' in err or 'usado' in err)

    def test_using_other_users_coupon_is_rejected(self):
        """BUG-006: Un usuario no puede usar el cupón asignado a otro cliente."""
        self.client.force_login(self.user_a)
        payload = {
            "nombre": "User A",
            "email": self.user_a.email,
            "producto_id": self.producto.id,
            "talla": "M",
            "cantidad": 1,
            "cupon": "SOLARY-USERB-15"  # Cupón de User B
        }
        resp = self.client.post('/api/crear-preorden/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("corresponde", resp.json().get('error', '').lower())


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class Bug007PrecioClpCrashTest(TestCase):
    def test_enviar_correo_with_zero_or_none_precio_total_does_not_crash(self):
        """
        BUG-007: Si orden.precio_total es 0 o falsy, enviar_correo_preorden
        no debe intentar acceder a orden.producto.precio_clp (que no existe)
        sino a orden.producto.precio, evitando AttributeError.
        """
        from locales.views import enviar_correo_preorden
        p = Producto.objects.create(nombre="Test Product", precio=150000, precio_usd=160)
        orden = PreOrden.objects.create(
            codigo_orden="SL-2026-9999",
            nombre_cliente="Crash Tester",
            email_cliente="crash@test.com",
            direccion_entrega="Santiago",
            producto=p,
            talla="M",
            cantidad=2,
            precio_total=0,  # Falsy, obliga a evaluar el fallback
            estado="CONFIRMADA"
        )
        # Esto lanzaba AttributeError: 'Producto' object has no attribute 'precio_clp'
        resultado = enviar_correo_preorden(orden)
        self.assertTrue(resultado)
        self.assertGreater(len(mail.outbox), 0)


class Bug009LocalBadgeBrandTest(TestCase):
    def test_local_badge_tipo_uses_solary_brand_not_trapstar(self):
        """
        BUG-009: El método badge_tipo() del modelo Local debe anteponer
        'SOLARY', nunca 'TRAPSTAR'.
        """
        from locales.models import Local
        local = Local.objects.create(nombre="Flagship La Serena", tipo="FLAGSHIP")
        self.assertEqual(local.badge_tipo(), "SOLARY FLAGSHIP")


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class Bug013TaxMathConsistencyTest(TestCase):
    def test_iva_and_neto_sum_matches_total_exactly(self):
        """
        BUG-013: El cálculo de IVA (19%) y Neto debe garantizar que
        neto_val + iva_val == total_val exactamente, sin descuadres de 1 peso.
        """
        from locales.views import enviar_correo_preorden
        montos_a_probar = [161492, 189990, 222000, 244990, 310000, 1048000]

        for total in montos_a_probar:
            p = Producto.objects.create(nombre=f"Prod {total}", precio=total, precio_usd=100)
            orden = PreOrden.objects.create(
                codigo_orden=f"SL-TAX-{total}",
                nombre_cliente="Tax Tester",
                email_cliente="tax@test.com",
                direccion_entrega="Santiago",
                producto=p,
                talla="M",
                cantidad=1,
                precio_total=total,
                estado="CONFIRMADA"
            )
            enviar_correo_preorden(orden)
            self.assertGreater(len(mail.outbox), 0)
            email_enviado = mail.outbox[-1]
            html_body = email_enviado.alternatives[0][0]

            # Verificamos matemáticamente la fórmula
            neto_val = round(total / 1.19)
            iva_val = total - neto_val
            self.assertEqual(neto_val + iva_val, total)

            # Verificamos que los textos formateados aparezcan en el correo
            subtotal_str = f"${total:,.0f} CLP".replace(',', '.')
            iva_str = f"${iva_val:,.0f} CLP".replace(',', '.')
            self.assertIn(subtotal_str, html_body)
            self.assertIn(iva_str, html_body)


class StoreAuthenticationBoundaryTests(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        self.user = User.objects.create_user(
            username='account-owner', email='owner@example.test', password='StrongPassphrase-2026!'
        )
        self.other_user = User.objects.create_user(
            username='other-owner', email='other@example.test', password='StrongPassphrase-2026!'
        )
        self.product = Producto.objects.create(nombre='Private catalog item', precio=125000, precio_usd=135)

    def test_guest_is_redirected_from_store_catalog_and_logistics(self):
        for path in ('/', '/productos/', f'/productos/{self.product.pk}/', '/locales/informacion/'):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response['Location'].startswith('/login/?next='))

    def test_guest_login_menu_hides_store_and_checkout_controls(self):
        response = self.client.get('/login/')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'class="sub-header"')
        self.assertNotContains(response, 'VAULT / SHOP')
        self.assertNotContains(response, 'PREVENTA &amp; LOGÍSTICA')
        self.assertNotContains(response, 'id="globalWishlistBtn"')
        self.assertNotContains(response, 'id="globalBagBtn"')
        self.assertNotContains(response, 'id="globalCheckoutForm"')

        self.client.force_login(self.user)
        authenticated_response = self.client.get('/perfil/')
        self.assertContains(authenticated_response, 'class="sub-header"')

    def test_guest_cannot_checkout_track_or_validate_private_coupon(self):
        purchase = self.client.post('/api/crear-preorden/', data='{}', content_type='application/json')
        tracking = self.client.get('/locales/api/rastrear/?codigo=SL-PRIVATE')
        coupon = self.client.get('/api/validar-cupon/?codigo=SOLARY15')
        self.assertEqual(purchase.status_code, 401)
        self.assertEqual(tracking.status_code, 401)
        self.assertEqual(coupon.status_code, 401)
        self.assertEqual(PreOrden.objects.count(), 0)

    def test_user_cannot_read_another_accounts_tracking_details(self):
        order = PreOrden.objects.create(
            codigo_orden='SL-OWNER-ONLY', usuario=self.other_user,
            nombre_cliente='Private Name', email_cliente=self.other_user.email,
            telefono_cliente='private-phone', direccion_entrega='private-address',
            producto=self.product, precio_total=self.product.precio,
        )
        self.client.force_login(self.user)
        response = self.client.get('/locales/api/rastrear/', {'codigo': order.codigo_orden})
        self.assertEqual(response.status_code, 404)
        self.assertNotIn('Private Name', response.content.decode())
        self.assertNotIn('private-address', response.content.decode())

    def test_customer_profile_only_lists_their_own_orders(self):
        own_order = PreOrden.objects.create(
            codigo_orden='SL-OWN-ORDERS', usuario=self.user,
            nombre_cliente='Account Owner', email_cliente=self.user.email,
            direccion_entrega='own-address', producto=self.product,
            precio_total=self.product.precio,
        )
        PreOrden.objects.create(
            codigo_orden='SL-OTHER-ORDERS', usuario=self.other_user,
            nombre_cliente='Other Customer', email_cliente=self.other_user.email,
            direccion_entrega='other-address', producto=self.product,
            precio_total=self.product.precio,
        )
        self.client.force_login(self.user)

        response = self.client.get('/perfil/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['ordenes']), [own_order])

    def test_matching_email_does_not_claim_unowned_historical_orders(self):
        legacy = PreOrden.objects.create(
            codigo_orden='SL-UNCLAIMED', nombre_cliente='Legacy Guest',
            email_cliente=self.user.email, direccion_entrega='private-address',
            producto=self.product, precio_total=self.product.precio,
        )
        self.client.force_login(self.user)
        response = self.client.get('/perfil/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['ordenes'].count(), 0)
        legacy.refresh_from_db()
        self.assertIsNone(legacy.usuario_id)

    def test_email_preview_is_not_public(self):
        response = self.client.get('/emails/')
        self.assertEqual(response.status_code, 302)





