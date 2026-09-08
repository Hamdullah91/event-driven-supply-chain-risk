from src.ml.event_classifier import EventClassifier


def main() -> None:
    classifier = EventClassifier(
        model_path="models/event_classifier/distilbert_supply_chain"
    )

    articles = [
        "A fire shut down production at a semiconductor fabrication plant.",
        "The government announced new export restrictions on advanced semiconductor manufacturing equipment.",
        "A shortage of critical battery materials disrupted production across several factories.",
        "Regulators introduced new environmental requirements for electric vehicle battery manufacturers.",
        "A trade embargo was imposed on advanced chip technology exports.",
        "A major supplier failed to deliver key aerospace components, delaying aircraft production.",
    ]

    for index, article in enumerate(articles, start=1):
        result = classifier.classify(article)
        probabilities = classifier.predict_proba(article)

        print(f"Event Type        : {result.event_type}")
        print(f"Confidence        : {result.confidence:.4f}")
        print(f"Second Event Type : {result.second_event_type}")
        print(f"Second Confidence : {result.second_confidence:.4f}")
        print(f"Confidence Margin : {result.confidence_margin:.4f}")
        print(f"Requires Review   : {result.requires_review}")

        for label, probability in sorted(
            probabilities.items(),
            key=lambda item: item[1],
            reverse=True,
        ):
            print(f"  {label:25} {probability:.4f}")

        print("-" * 60)


if __name__ == "__main__":
    main()