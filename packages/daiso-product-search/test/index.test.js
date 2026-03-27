const test = require("node:test")
const assert = require("node:assert/strict")
const fs = require("node:fs")
const path = require("node:path")

const {
  getOnlineStock,
  getStoreDetail,
  getStorePickupStock,
  lookupStoreProductAvailability,
  searchProducts,
  searchStores
} = require("../src/index")
const {
  buildSearchGoodsParams,
  normalizeSearchGoodsResponse,
  normalizeStorePickupStockResponse,
  normalizeStoreSearchResponse
} = require("../src/parse")

const fixturesDir = path.join(__dirname, "fixtures")
const storeSearchPayload = JSON.parse(fs.readFileSync(path.join(fixturesDir, "store-search.json"), "utf8"))
const searchGoodsPayload = JSON.parse(fs.readFileSync(path.join(fixturesDir, "search-goods.json"), "utf8"))
const storeDetailPayload = JSON.parse(fs.readFileSync(path.join(fixturesDir, "store-detail.json"), "utf8"))
const storePickupStockPayload = JSON.parse(fs.readFileSync(path.join(fixturesDir, "store-pickup-stock.json"), "utf8"))
const onlineStockPayload = JSON.parse(fs.readFileSync(path.join(fixturesDir, "online-stock.json"), "utf8"))

test("normalizeStoreSearchResponse prefers the closest exact-name store match", () => {
  const items = normalizeStoreSearchResponse(storeSearchPayload, "강남역2호점")

  assert.equal(items[0].strCd, "10224")
  assert.equal(items[0].name, "강남역2호점")
  assert.equal(items[0].pickupAvailable, true)
  assert.equal(items[0].openTime, "10:00")
})

test("buildSearchGoodsParams keeps the official SearchGoods query contract", () => {
  assert.deepEqual(buildSearchGoodsParams("리들샷", { limit: 30, pickupOnly: true }), {
    searchTerm: "리들샷",
    searchQuery: "",
    pageNum: "1",
    brndCd: "",
    cntPerPage: "30",
    userId: "",
    newPdYn: "",
    massOrPsblYn: "",
    pkupOrPsblYn: "Y",
    fdrmOrPsblYn: "",
    quickOrPsblYn: "",
    searchSort: "",
    isCategory: "1"
  })
})

test("normalizeSearchGoodsResponse surfaces reusable product candidates", () => {
  const result = normalizeSearchGoodsResponse(searchGoodsPayload, "VT 리들샷 100")

  assert.equal(result.totalSize, 25)
  assert.equal(result.relationKeyword, "리들,앰플,브이티")
  assert.equal(result.items[0].pdNo, "1049275")
  assert.equal(result.items[0].brand.displayName, "VT")
  assert.equal(result.items[0].pickupAvailable, true)
})

test("normalizeStorePickupStockResponse maps stock rows into a public availability shape", () => {
  const stock = normalizeStorePickupStockResponse(storePickupStockPayload, {
    pdNo: "1049275",
    strCd: "10224"
  })

  assert.equal(stock.quantity, 3)
  assert.equal(stock.inStock, true)
  assert.equal(stock.saleStatusCode, "1")
})

test("public client helpers can consume injected fetch fixtures", async () => {
  const originalFetch = global.fetch

  global.fetch = async (url) => {
    if (String(url).includes("/api/ms/msg/selStr") && !String(url).includes("selStrInfo")) {
      return makeResponse(storeSearchPayload)
    }

    if (String(url).includes("/ssn/search/SearchGoods")) {
      return makeResponse(searchGoodsPayload)
    }

    if (String(url).includes("/api/dl/dla-api/selStrInfo")) {
      return makeResponse(storeDetailPayload)
    }

    if (String(url).includes("/api/pd/pdh/selStrPkupStck")) {
      return makeResponse(storePickupStockPayload)
    }

    if (String(url).includes("/api/pdo/selOnlStck")) {
      return makeResponse(onlineStockPayload)
    }

    return new Response("not found", { status: 404 })
  }

  try {
    const storeResult = await searchStores("강남역2호점")
    assert.equal(storeResult.items[0].strCd, "10224")

    const productResult = await searchProducts("VT 리들샷 100")
    assert.equal(productResult.items[0].pdNo, "1049275")

    const storeDetail = await getStoreDetail("10224")
    assert.equal(storeDetail.data.onlStrYn, "Y")

    const pickupStock = await getStorePickupStock({ pdNo: "1049275", strCd: "10224" })
    assert.equal(pickupStock.quantity, 3)

    const onlineStock = await getOnlineStock({ pdNo: "1049275" })
    assert.equal(onlineStock.quantity, 13047)

    const availability = await lookupStoreProductAvailability({
      storeQuery: "강남역2호점",
      productQuery: "VT 리들샷 100"
    })
    assert.equal(availability.selectedStore.strCd, "10224")
    assert.equal(availability.selectedProduct.pdNo, "1049275")
    assert.equal(availability.pickupStock.quantity, 3)
    assert.equal(availability.onlineStock.quantity, 13047)
  } finally {
    global.fetch = originalFetch
  }
})

function makeResponse(body) {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: {
      "content-type": "application/json"
    }
  })
}
