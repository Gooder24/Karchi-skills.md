import { expect, test } from "bun:test";
import { fix, missing } from "./pevne-medzery";

const show = (s: string) => fix(s).replaceAll(" ", "°");

test("one-letter words, invoice numbers, sums and dates", () => {
  expect(show("Žiadame Vás o zaslanie katalógu a cenníka v čo najkratšom čase.")).toBe(
    "Žiadame Vás o°zaslanie katalógu a°cenníka v°čo najkratšom čase.",
  );
  expect(show("faktúru č. 567/2026 vo výške 1 560 eur zo dňa 10. novembra 2026")).toBe(
    "faktúru č.°567/2026 vo výške 1°560°eur zo dňa 10.°novembra 2026",
  );
  expect(show("1 800,00 € a zľavu 10 % do 7 dní, splatná 10. 10. 2026")).toBe(
    "1°800,00°€ a°zľavu 10°% do 7°dní, splatná 10.°10.°2026",
  );
  expect(show("Ing. Novák z firmy eSYST, s. r. o.")).toBe("Ing.°Novák z°firmy eSYST,°s.°r.°o.");
  expect(show("podľa § 5 ods. 2 a čl. 3, na s. 4")).toBe("podľa §°5 ods.°2 a°čl.°3, na s.°4");
});

test("leaves ordinary spaces alone", () => {
  expect(show("Na základe Vašej ponuky objednávame 2026 kusov.")).toBe("Na základe Vašej ponuky objednávame 2026 kusov.");
  expect(show("Tovar sme odoslali včera.")).toBe("Tovar sme odoslali včera.");
  expect(show("Dodali sme tovar typu B. Ďalej žiadame o výmenu.")).toBe("Dodali sme tovar typu B. Ďalej žiadame o°výmenu.");
  expect(show("Firma X, a. s. zastupuje")).toBe("Firma X,°a.°s. zastupuje");
  expect(show("od roku 2010 spolupracujeme")).toBe("od roku 2010 spolupracujeme");
  expect(show("Objednávame 3 100-litrové sudy.")).toBe("Objednávame 3 100-litrové sudy.");
});

test("check finds what fix would change, and nothing after fix", () => {
  const text = "Reklamujeme dodávku a žiadame o výmenu.";
  expect(missing(text).length).toBe(2);
  expect(missing(fix(text))).toEqual([]);
});
