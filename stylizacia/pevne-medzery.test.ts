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
});

test("leaves ordinary spaces alone", () => {
  expect(show("Na základe Vašej ponuky objednávame 2026 kusov.")).toBe("Na základe Vašej ponuky objednávame 2026 kusov.");
  expect(show("Tovar sme odoslali včera.")).toBe("Tovar sme odoslali včera.");
});

test("check finds what fix would change, and nothing after fix", () => {
  const text = "Reklamujeme dodávku a žiadame o výmenu.";
  expect(missing(text).length).toBe(2);
  expect(missing(fix(text))).toEqual([]);
});
