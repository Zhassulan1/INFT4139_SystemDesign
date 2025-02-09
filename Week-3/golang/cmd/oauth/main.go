// Crazy 60k rps on single instance
// 40k rps on 3 instances
package main

import (
	"context"
	"crypto/md5"
	"encoding/hex"
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/golang-jwt/jwt"
	"github.com/jackc/pgx/v4/pgxpool"
	"github.com/joho/godotenv"
	"github.com/valyala/fasthttp"

	"github.com/fasthttp/router"
	"github.com/go-redis/redis/v8"
)

// Global Variables

var (
	dbPool      *pgxpool.Pool
	redisClient *redis.Client
	secretKey   string
	hashSalt    string
)

const expireTime = 3600
const refreshThreshold time.Duration = time.Duration(expireTime) * time.Second / 4

// Data Models

// request/response structures
type UserRegister struct {
	Name     string `json:"name"`
	Password string `json:"password"`
	Scopes   string `json:"scopes"`
}

type TokenRequest struct {
	UserID   int    `json:"user_id"`
	Password string `json:"password"`
}

type TokenResponse struct {
	AccessToken string `json:"access_token"`
}

// JWT token fields
type CustomClaims struct {
	UserID int    `json:"user_id"`
	Name   string `json:"name"`
	Scopes string `json:"scopes"`
	jwt.StandardClaims
}

func computeMD5(password string) string {
	h := md5.New()
	h.Write([]byte(hashSalt + password))
	return hex.EncodeToString(h.Sum(nil))
}

// Creates a JWT token with the payload and expiration
func createAccessToken(userID int, name, scopes string) (string, error) {
	now := time.Now().UTC()
	claims := CustomClaims{
		UserID: userID,
		Name:   name,
		Scopes: scopes,
		StandardClaims: jwt.StandardClaims{
			ExpiresAt: now.Add(time.Duration(expireTime) * time.Second).Unix(),
			IssuedAt:  now.Unix(),
		},
	}

	var signingMethod jwt.SigningMethod = jwt.SigningMethodHS256

	token := jwt.NewWithClaims(signingMethod, claims)
	tokenString, err := token.SignedString([]byte(secretKey))
	if err != nil {
		return "", err
	}
	return tokenString, nil
}

func writeJSON(ctx *fasthttp.RequestCtx, statusCode int, data interface{}) {
	ctx.SetStatusCode(statusCode)
	ctx.Response.Header.Set("Content-Type", "application/json")
	js, err := json.Marshal(data)
	if err != nil {
		log.Printf("JSON marshal error: %v", err)
		ctx.SetStatusCode(fasthttp.StatusInternalServerError)
		return
	}
	ctx.Write(js)
}

// HTTP Handlers

// POST /user
func registerUser(ctx *fasthttp.RequestCtx) {
	var req UserRegister
	if err := json.Unmarshal(ctx.PostBody(), &req); err != nil {
		writeJSON(ctx, fasthttp.StatusBadRequest, map[string]string{"error": "Invalid request body"})
		return
	}

	// Default scopes if not provided
	if req.Scopes == "" {
		req.Scopes = "user"
	}

	hashedPassword := computeMD5(req.Password)

	var userID int
	query := `INSERT INTO users (name, password, scopes) VALUES ($1, $2, $3) RETURNING id`
	err := dbPool.QueryRow(context.Background(), query, req.Name, hashedPassword, req.Scopes).Scan(&userID)
	if err != nil {
		log.Printf("DB error: %v", err)
		writeJSON(ctx, fasthttp.StatusInternalServerError, map[string]string{"error": "DB error"})
		return
	}

	resp := map[string]interface{}{
		"user_id": userID,
		"name":    req.Name,
		"scopes":  req.Scopes,
	}
	writeJSON(ctx, fasthttp.StatusOK, resp)
}

// POST /token
func accessToken(ctx *fasthttp.RequestCtx) {
	var req TokenRequest
	if err := json.Unmarshal(ctx.PostBody(), &req); err != nil {
		writeJSON(ctx, fasthttp.StatusBadRequest, map[string]string{"error": "Invalid request body"})
		return
	}

	// Query the user from the DB
	var (
		userID   int
		password string
		name     string
		scopes   string
	)
	query := `SELECT id, password, name, scopes FROM users WHERE id = $1`
	err := dbPool.QueryRow(context.Background(), query, req.UserID).Scan(&userID, &password, &name, &scopes)
	if err != nil {
		writeJSON(ctx, fasthttp.StatusUnauthorized, map[string]string{"error": "Unauthorized"})
		return
	}

	// Compare hashed password
	if computeMD5(req.Password) != password {
		writeJSON(ctx, fasthttp.StatusUnauthorized, map[string]string{"error": "Unauthorized"})
		return
	}

	// Redis keys: userID->token and token->userID
	userKey := strconv.Itoa(userID)
	// Check if a token already exists
	oldToken, err := redisClient.Get(context.Background(), userKey).Result()
	if err == nil && oldToken != "" {
		// Check TTL of the token key
		ttl, err := redisClient.TTL(context.Background(), oldToken).Result()
		if err == nil && ttl > 0 && ttl < refreshThreshold {
			// Refresh token if TTL is less than threshold
			newToken, err := createAccessToken(userID, name, scopes)
			if err != nil {
				writeJSON(ctx, fasthttp.StatusInternalServerError, map[string]string{"error": "Token creation error"})
				return
			}
			// Set new token
			redisClient.SetEX(context.Background(), newToken, userKey, time.Duration(expireTime)*time.Second)
			redisClient.SetEX(context.Background(), userKey, newToken, time.Duration(expireTime)*time.Second)
			writeJSON(ctx, fasthttp.StatusOK, TokenResponse{AccessToken: newToken})
			return
		}
		writeJSON(ctx, fasthttp.StatusOK, TokenResponse{AccessToken: oldToken})
		return
	}

	// Token doesn't exists, create new
	newToken, err := createAccessToken(userID, name, scopes)
	if err != nil {
		writeJSON(ctx, fasthttp.StatusInternalServerError, map[string]string{"error": "Token creation error"})
		return
	}
	// Store token and mapping in Redis
	redisClient.SetEX(context.Background(), newToken, userKey, time.Duration(expireTime)*time.Second)
	redisClient.SetEX(context.Background(), userKey, newToken, time.Duration(expireTime)*time.Second)

	writeJSON(ctx, fasthttp.StatusOK, TokenResponse{AccessToken: newToken})
}

// GET /check
func checkToken(ctx *fasthttp.RequestCtx) {
	// Extract Authorization header
	authHeader := string(ctx.Request.Header.Peek("Authorization"))
	if !strings.HasPrefix(authHeader, "Bearer ") {
		writeJSON(ctx, fasthttp.StatusUnauthorized, map[string]interface{}{"status": "inactive", "scope": nil})
		return
	}
	tokenString := strings.TrimPrefix(authHeader, "Bearer ")
	if tokenString == "" {
		writeJSON(ctx, fasthttp.StatusUnauthorized, map[string]interface{}{"status": "inactive", "scope": nil})
		return
	}

	// Parse the token
	claims := &CustomClaims{}
	parsedToken, err := jwt.ParseWithClaims(tokenString, claims, func(token *jwt.Token) (interface{}, error) {
		return []byte(secretKey), nil
	})
	if err != nil {
		// If token expired or invalid, report inactive
		writeJSON(ctx, fasthttp.StatusOK, map[string]interface{}{"status": "inactive", "scope": nil})
		return
	}
	if !parsedToken.Valid {
		writeJSON(ctx, fasthttp.StatusOK, map[string]interface{}{"status": "inactive", "scope": nil})
		return
	}

	// Check that the payload contains required fields
	if claims.Scopes == "" || claims.UserID == 0 {
		writeJSON(ctx, fasthttp.StatusOK, map[string]interface{}{"status": "inactive", "scope": nil})
		return
	}

	// Verify the token is still stored in Redis
	storedUserKey, err := redisClient.Get(context.Background(), tokenString).Result()
	if err != nil {
		writeJSON(ctx, fasthttp.StatusOK, map[string]interface{}{"status": "inactive", "scope": nil})
		return
	}
	if storedUserKey != strconv.Itoa(claims.UserID) {
		writeJSON(ctx, fasthttp.StatusOK, map[string]interface{}{"status": "inactive", "scope": nil})
		return
	}

	// Token is valid and active
	writeJSON(ctx, fasthttp.StatusOK, map[string]interface{}{"status": "active", "scope": claims.Scopes})
}

// Entry point
func main() {

	// Load .env file
	if err := godotenv.Load(); err != nil {
		log.Println("No .env file found - using environment variables")
	}

	// Read .env
	secretKey = os.Getenv("SECRET")
	hashSalt = os.Getenv("HASH_SALT")

	dbUser := os.Getenv("DB_USER")
	dbPassword := os.Getenv("DB_PASSWORD")
	dbHost := os.Getenv("DB_HOST")
	dbPort := os.Getenv("DB_PORT")
	dbName := os.Getenv("DB_NAME")

	// Construct the connection string
	connStr := fmt.Sprintf("postgresql://%s:%s@%s:%s/%s",
		dbUser, dbPassword, dbHost, dbPort, dbName)

	var err error
	dbPool, err = pgxpool.Connect(context.Background(), connStr)
	if err != nil {
		log.Fatalf("Unable to create DB pool: %v", err)
	}
	defer dbPool.Close()
	log.Println("Postgres pool created")

	// Redis pool
	redisClient = redis.NewClient(&redis.Options{
		Addr:     "localhost:6379",
		DB:       0,
		PoolSize: 1000,
	})
	// Test Redis connection
	if err := redisClient.Ping(context.Background()).Err(); err != nil {
		log.Fatalf("Unable to connect to Redis: %v", err)
	}
	log.Println("Redis client connected")

	// Set up the router
	r := router.New()
	r.POST("/user", registerUser)
	r.POST("/token", accessToken)
	r.GET("/check", checkToken)

	var port = flag.String("port", "8001", "API server port")
	flag.Parse()

	addr := ":" + *port
	log.Printf("Server is listening on %s", addr)
	if err := fasthttp.ListenAndServe(addr, r.Handler); err != nil {
		log.Fatalf("Error in ListenAndServe: %v", err)
	}
}
