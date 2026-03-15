from database import db
from datetime import datetime, timezone

class TaxiEvent(db.Model):
    __tablename__ = "taxi_trips"

    id = db.Column(db.Integer, primary_key=True)
    vendorid = db.Column(db.Integer)
    pulocationid = db.Column(db.Integer, index=True)    #pickup
    dolocationid = db.Column(db.Integer, index=True)    #dropoff
    passenger_count = db.Column(db.Float)
    trip_distance = db.Column(db.Float)
    fare_amount = db.Column(db.Float)
    total_amount = db.Column(db.Float)
    payment_type = db.Column(db.Integer)
    congestion_surcharge = db.Column(db.Float)
    ratecodeid = db.Column(db.Float)

class AdageDataset(db.Model):
    __tablename__ = "adage_datasets"

    id = db.Column(db.Integer, primary_key=True)
    data_source = db.Column(db.String, nullable=False)
    dataset_type = db.Column(db.String, nullable=False)
    dataset_id = db.Column(db.String)
    # timestamp stuff from collectNYCTaxi
    timestamp = db.Column(db.String)
    timezone = db.Column(db.String)
    # collected_at = db.Column(db.DateTime(timezone=True),)

    # events [] section
    # events = db.relationship("AdageEvent", backref="dataset")
