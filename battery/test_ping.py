from optimization_service.src.worker import celery_app
i = celery_app.control.inspect()
print("active:", i.active())
