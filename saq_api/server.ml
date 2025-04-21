(* server.ml *)
module type DB = Caqti_lwt.CONNECTION
module T = Caqti_type

(* open Lwt.Syntax
open Yojson.Safe *)

(* Define the product type *)
type product = {
  code_saq : string;
  name : string;
  url : string;
  product_type : string;
  volume : string;
  country : string;
  rating_pct : int option;
  reviews_count : int;
  discounted : bool;
  discount_pct : string;
  price : float;
  old_price : float;
  available_online : bool;
  available_instore : bool;
  (* categories : Yojson.Safe.t; *)
}

let product_type : product T.t =
  let open T in
  let nested_tuple = 
  (t2 (
    t12 string string string string string string (option int) int bool string float float) 
    (t2 bool bool)
  ) in
  let encode = (fun p ->
    Ok (( p.code_saq, p.name, p.url, p.product_type, p.volume, p.country,
      p.rating_pct, p.reviews_count, p.discounted, p.discount_pct,
      p.price, p.old_price), (p.available_online, p.available_instore)
    ))
  in
  let decode = (fun (( code_saq, name, url, product_type, volume, country,
                  rating_pct, reviews_count, discounted, discount_pct,
                  price, old_price), (available_online, available_instore)) ->
    Ok {
      code_saq; name; url; product_type; volume; country;
      rating_pct; reviews_count; discounted; discount_pct;
      price; old_price; available_online; available_instore;
    })
  in
  custom ~encode:encode ~decode:decode nested_tuple

let int_or_null bleh =
  match bleh with
  | Some i -> `Int i
  | None -> `Null

let product_to_yojson p =
  `Assoc [
    "code_saq", `String p.code_saq;
    "name", `String p.name;
    "url", `String p.url;
    "type", `String p.product_type;
    "volume", `String p.volume;
    "country", `String p.country;
    "rating_pct", int_or_null p.rating_pct;
    "reviews_count", `Int p.reviews_count;
    "discounted", `Bool p.discounted;
    "discount_pct", `String p.discount_pct;
    "price", `Float p.price;
    "old_price", `Float p.old_price;
    "available_online", `Bool p.available_online;
    "available_instore", `Bool p.available_instore;
    (* "categories", p.categories; *)
    (* "categories", Yojson.Safe.from_string product.categories; *)
  ]

(* Queries *)
let list_products orderBy dir =
  let query =
    let open Caqti_request.Infix in
    (T.unit ->* product_type)
    ("SELECT code_saq, name, url, type, volume, country, rating_pct, reviews_count, \
      discounted, discount_pct, price, old_price, available_online, available_instore
      FROM products 
      ORDER BY " ^ orderBy ^ " " ^ dir ^ " LIMIT 10") in
  let pattern =
    Caqti_query.show (Caqti_request.query query Caqti_driver_info.dummy)
  in
  Dream.log "generated query: %s" pattern;
  fun (module Db : DB) -> 
    let%lwt products_or_error = Db.collect_list query () in
    Caqti_lwt.or_fail products_or_error

let find_product_by_code =
  let query =
    let open Caqti_request.Infix in
    (T.string ->? product_type)
    "SELECT code_saq, name, url, type, volume, country, rating_pct, reviews_count, \
            discounted, discount_pct, price, old_price, available_online, available_instore
      FROM products WHERE code_saq = ($1)"
  in
  fun code_saq (module Db : DB) ->
    let%lwt products_or_error = Db.find_opt query code_saq in
    Caqti_lwt.or_fail products_or_error

(* GET /products *)
let get_products = (fun request ->
  let orderBy = match Dream.query request "orderBy" with
    | Some "code_saq" -> "code_saq"
    | Some "name" -> "name"
    | Some "url" -> "url"
    | Some "product_type" -> "product_type"
    | Some "volume" -> "volume"
    | Some "country" -> "country"
    | Some "rating_pct" -> "rating_pct"
    | Some "reviews_count" -> "reviews_count"
    | Some "discounted" -> "discounted"
    | Some "discount_pct" -> "discount_pct"
    | Some "price" -> "price"
    | Some "old_price" -> "old_price"
    | Some "available_online" -> "available_online"
    | Some "available_instore" -> "available_instore"
    | _ -> "price"
  in
  let dir = match Dream.query request "dir" with
    | Some "asc" -> "ASC"
    | _ -> "DESC"
  in
  let%lwt result = 
    Dream.sql request (list_products orderBy dir)
  in
  let products = `List (List.map product_to_yojson result) in
  Dream.json (Yojson.Safe.to_string products)
  )

(* GET /products/:code_saq *)
let get_product = (fun request ->
  let%lwt result = 
    Dream.sql request (find_product_by_code (Dream.param request "code_saq")) 
  in
  match result with
  | Some product ->
      Dream.json (Yojson.Safe.to_string (product_to_yojson product))
  | None ->
      Dream.respond ~status:`Not_Found "Product not found"
  (* | Error err ->
      Dream.log "DB error: %s" (Caqti_error.show err);
      Dream.respond ~status:`Internal_Server_Error "Internal server error" *)
  )

open Dream_middleware_ext.Cors

(* allow all verb headers *)
let all_verb_headers = all_verbs_header ()

(* make conf: allow wildcard origin *)
let allow_wildcard_conf =
  make_cors_conf ~allowed_origin:WildCard ~allowed_methods:all_verb_headers
    ~allowed_headers:[ "X-Requested-With" ] ~expose_headers:[ "GET" ] ()

(* make allow wildcard middle or with other confs *)
let cors_middleware = make_cors allow_wildcard_conf

let add_header inner_handler request =
  let rep : Dream.response Lwt.t = inner_handler request in
  let%lwt rep = rep in
  Dream.add_header rep "Access-Control-Allow-Origin" "*"; 
  Utils.print_all_headers rep;
  Lwt.return rep

let () =
  (* Uncomment to use the debug error handler *)
  (* Dream.run ~error_handler:Dream.debug_error_handler *)
  Dream.run
  @@ cors_middleware (* should apply CORS middileware at outmost level*)
  @@ add_header
  @@ Dream.logger
  @@ Dream.sql_pool "postgresql://postgres:testing@localhost/saq_db"
  @@ Dream.router [
  
    Dream.get "/"
      (fun request ->
        Dream.log "Sending greeting to %s!" (Dream.client request);
        Dream.html "Good morning, world!");

    Dream.get "/products" get_products;

    Dream.get "/products/:code_saq" get_product;
  ]